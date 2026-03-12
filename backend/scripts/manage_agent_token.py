"""CLI script to get or update (rotate) an Agent authentication token.

Usage:
    # Show token status for an agent by ID
    uv run python scripts/manage_agent_token.py --agent-id <UUID>

    # Rotate token for an agent (generates new token and prints it)
    uv run python scripts/manage_agent_token.py --agent-id <UUID> --rotate

    # List agents for a board
    uv run python scripts/manage_agent_token.py --board-id <UUID> --list

    # Rotate token for the board lead agent
    uv run python scripts/manage_agent_token.py --board-id <UUID> --lead --rotate

    # Verify a token against an agent
    uv run python scripts/manage_agent_token.py --agent-id <UUID> --verify <TOKEN>
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from uuid import UUID

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Get or update Agent authentication tokens.",
    )
    parser.add_argument(
        "--agent-id",
        type=str,
        default=None,
        help="Agent UUID to inspect or update",
    )
    parser.add_argument(
        "--board-id",
        type=str,
        default=None,
        help="Board UUID to filter agents",
    )
    parser.add_argument(
        "--gateway-id",
        type=str,
        default=None,
        help="Gateway UUID to filter agents",
    )
    parser.add_argument(
        "--lead",
        action="store_true",
        help="Target the board lead agent (requires --board-id)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        dest="list_agents",
        help="List agents matching the filter criteria",
    )
    parser.add_argument(
        "--rotate",
        action="store_true",
        help="Generate a new token for the agent (prints the raw token)",
    )
    parser.add_argument(
        "--verify",
        type=str,
        default=None,
        metavar="TOKEN",
        help="Verify a token against the agent's stored hash",
    )
    return parser.parse_args()


async def _list_agents(
    *,
    board_id: UUID | None,
    gateway_id: UUID | None,
) -> int:
    """List agents matching the given filter criteria."""
    from sqlmodel import col, select

    from app.db.session import async_session_maker
    from app.models.agents import Agent

    async with async_session_maker() as session:
        statement = select(Agent)
        if board_id:
            statement = statement.where(col(Agent.board_id) == board_id)
        if gateway_id:
            statement = statement.where(col(Agent.gateway_id) == gateway_id)
        statement = statement.order_by(col(Agent.name))

        agents = list(await session.exec(statement))

        if not agents:
            sys.stdout.write("No agents found matching the criteria.\n")
            return 0

        sys.stdout.write(f"Found {len(agents)} agent(s):\n\n")
        for agent in agents:
            has_token = "yes" if agent.agent_token_hash else "no"
            lead_marker = " [LEAD]" if agent.is_board_lead else ""
            main_marker = ""
            if agent.board_id is None:
                main_marker = " [MAIN]"
            sys.stdout.write(
                f"  ID: {agent.id}\n"
                f"  Name: {agent.name}{lead_marker}{main_marker}\n"
                f"  Board ID: {agent.board_id or 'N/A (gateway main)'}\n"
                f"  Gateway ID: {agent.gateway_id}\n"
                f"  Status: {agent.status}\n"
                f"  Has Token: {has_token}\n"
                f"  Last Seen: {agent.last_seen_at or 'never'}\n"
                "\n"
            )
        return 0


async def _get_agent_by_id(agent_id: UUID) -> object | None:
    """Retrieve an agent by ID."""
    from app.db.session import async_session_maker
    from app.models.agents import Agent

    async with async_session_maker() as session:
        return await session.get(Agent, agent_id)


async def _get_board_lead(board_id: UUID) -> object | None:
    """Retrieve the board lead agent for a board."""
    from sqlmodel import col, select

    from app.db.session import async_session_maker
    from app.models.agents import Agent

    async with async_session_maker() as session:
        return (
            await session.exec(
                select(Agent)
                .where(col(Agent.board_id) == board_id)
                .where(col(Agent.is_board_lead).is_(True))
            )
        ).first()


async def _show_agent_token_status(agent_id: UUID) -> int:
    """Show the token status for an agent."""
    from app.models.agents import Agent

    agent = await _get_agent_by_id(agent_id)
    if agent is None or not isinstance(agent, Agent):
        sys.stderr.write(f"Agent not found: {agent_id}\n")
        return 1

    has_token = bool(agent.agent_token_hash)
    lead_marker = " [LEAD]" if agent.is_board_lead else ""
    main_marker = " [MAIN]" if agent.board_id is None else ""

    sys.stdout.write(f"Agent: {agent.name}{lead_marker}{main_marker}\n")
    sys.stdout.write(f"ID: {agent.id}\n")
    sys.stdout.write(f"Board ID: {agent.board_id or 'N/A (gateway main)'}\n")
    sys.stdout.write(f"Gateway ID: {agent.gateway_id}\n")
    sys.stdout.write(f"Status: {agent.status}\n")
    sys.stdout.write(f"Has Token Hash: {'yes' if has_token else 'no'}\n")
    if has_token and agent.agent_token_hash:
        # Show a prefix of the hash for debugging (not the full hash)
        hash_prefix = agent.agent_token_hash[:40] + "..."
        sys.stdout.write(f"Token Hash (prefix): {hash_prefix}\n")
    sys.stdout.write(f"Last Seen: {agent.last_seen_at or 'never'}\n")
    sys.stdout.write(f"Updated At: {agent.updated_at}\n")

    return 0


async def _rotate_agent_token(agent_id: UUID) -> int:
    """Rotate the authentication token for an agent."""
    from app.db.session import async_session_maker
    from app.models.agents import Agent
    from app.services.openclaw.db_agent_state import mint_agent_token

    async with async_session_maker() as session:
        agent = await session.get(Agent, agent_id)
        if agent is None or not isinstance(agent, Agent):
            sys.stderr.write(f"Agent not found: {agent_id}\n")
            return 1

        lead_marker = " [LEAD]" if agent.is_board_lead else ""
        main_marker = " [MAIN]" if agent.board_id is None else ""

        # Generate new token
        raw_token = mint_agent_token(agent)
        from app.core.time import utcnow

        agent.updated_at = utcnow()
        session.add(agent)
        await session.commit()
        await session.refresh(agent)

        sys.stdout.write(f"Token rotated for: {agent.name}{lead_marker}{main_marker}\n")
        sys.stdout.write(f"Agent ID: {agent.id}\n")
        sys.stdout.write(f"Board ID: {agent.board_id or 'N/A (gateway main)'}\n")
        sys.stdout.write(f"Gateway ID: {agent.gateway_id}\n")
        sys.stdout.write("\n")
        sys.stdout.write("=== NEW TOKEN (save this, it cannot be retrieved later) ===\n")
        sys.stdout.write(f"{raw_token}\n")
        sys.stdout.write("=============================================================\n")
        sys.stdout.write("\n")
        sys.stdout.write("Use this token with:\n")
        sys.stdout.write("  - Header: X-Agent-Token: <token>\n")
        sys.stdout.write("  - Or: Authorization: Bearer <token>\n")

        return 0


async def _verify_agent_token(agent_id: UUID, token: str) -> int:
    """Verify a token against an agent's stored hash."""
    from app.core.agent_tokens import verify_agent_token
    from app.models.agents import Agent

    agent = await _get_agent_by_id(agent_id)
    if agent is None or not isinstance(agent, Agent):
        sys.stderr.write(f"Agent not found: {agent_id}\n")
        return 1

    if not agent.agent_token_hash:
        sys.stderr.write(f"Agent {agent.name} has no token hash stored.\n")
        return 1

    is_valid = verify_agent_token(token, agent.agent_token_hash)

    lead_marker = " [LEAD]" if agent.is_board_lead else ""
    sys.stdout.write(f"Agent: {agent.name}{lead_marker}\n")
    sys.stdout.write(f"Agent ID: {agent.id}\n")
    sys.stdout.write(f"Token Valid: {'YES ✓' if is_valid else 'NO ✗'}\n")

    return 0 if is_valid else 1


async def _run() -> int:
    args = _parse_args()

    # Validate arguments
    if args.lead and not args.board_id:
        sys.stderr.write("--lead requires --board-id\n")
        return 1

    if args.list_agents:
        board_id = UUID(args.board_id) if args.board_id else None
        gateway_id = UUID(args.gateway_id) if args.gateway_id else None
        return await _list_agents(board_id=board_id, gateway_id=gateway_id)

    # Determine target agent
    target_agent_id: UUID | None = None

    if args.agent_id:
        target_agent_id = UUID(args.agent_id)
    elif args.lead and args.board_id:
        from app.models.agents import Agent

        board_id = UUID(args.board_id)
        lead = await _get_board_lead(board_id)
        if lead is None or not isinstance(lead, Agent):
            sys.stderr.write(f"No board lead found for board: {board_id}\n")
            return 1
        target_agent_id = lead.id
    else:
        sys.stderr.write(
            "Specify --agent-id, --list, or --board-id with --lead\n"
            "Run with --help for usage.\n"
        )
        return 1

    # Execute requested action
    if args.verify:
        return await _verify_agent_token(target_agent_id, args.verify)
    elif args.rotate:
        return await _rotate_agent_token(target_agent_id)
    else:
        return await _show_agent_token_status(target_agent_id)


def main() -> None:
    """Run the async CLI workflow and exit with its return code."""
    raise SystemExit(asyncio.run(_run()))


if __name__ == "__main__":
    main()
