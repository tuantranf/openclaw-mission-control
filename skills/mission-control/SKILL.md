---
name: mission-control
description: Mission Control API for creating, updating, comment and managing tasks, task thread, and boards.
homepage: http://127.0.0.1:8000
metadata: {"clawdbot":{"emoji":"📝"}}
---

# mission-control

Use the Mission Control API for creating, updating, commenting and managing tasks, task threads, and boards.

## Environment Setup

Before running any script, export these values from your `TOOLS.md`:

```bash
export BASE_URL="<value from TOOLS.md>"
export AUTH_TOKEN="<value from TOOLS.md>"
export BOARD_ID="<value from TOOLS.md>"
export AGENT_NAME="<value from TOOLS.md>"
export AGENT_ID="<value from TOOLS.md>"
```

Requirements: Node.js >= 18 (uses native `fetch` — no `npm install` needed).

## Available Scripts

| Script | Purpose | Required args | Optional args |
|--------|---------|--------------|---------------|
| `heartbeat.js` | Check in / report liveness | — | `--status healthy\|working\|idle` |
| `get-board.js` | Fetch board metadata | — | — |
| `get-tasks.js` | List board tasks | — | `--status inbox\|in_progress\|review\|done` |
| `create-task.js` | Create a new task | `--title` | `--description`, `--status`, `--priority`, `--assigned-agent-id` |
| `update-task.js` | Update task status or assignment | `--task-id` + at least one of: | `--status`, `--assigned-agent-id` |
| `close-task.js` | Close a task (sets status to `done`) | `--task-id` | — |
| `add-comment.js` | Post a comment on a task | `--task-id`, `--message` | — |

All scripts print JSON to stdout on success (exit 0) and an error message to stderr on failure (exit 1).

## Common Operations

### Heartbeat check-in

```bash
node skills/mission-control/heartbeat.js
# or with explicit status:
node skills/mission-control/heartbeat.js --status working
```

### Get board information

```bash
node skills/mission-control/get-board.js
```

### Get board tasks

```bash
# All tasks
node skills/mission-control/get-tasks.js

# Filter by status
node skills/mission-control/get-tasks.js --status inbox

# Pipe to jq for filtering
node skills/mission-control/get-tasks.js | jq '.[] | select(.status=="inbox")'
```

### Create a new task

```bash
node skills/mission-control/create-task.js --title "Investigate auth failure"

# With optional fields
node skills/mission-control/create-task.js \
  --title "Investigate auth failure" \
  --description "Users getting 401 on /login" \
  --status inbox \
  --priority high \
  --assigned-agent-id "<agent-id>"
```

### Update task status

```bash
node skills/mission-control/update-task.js --task-id <task-id> --status in_progress
node skills/mission-control/update-task.js --task-id <task-id> --status review
```

### Update task assignment

```bash
node skills/mission-control/update-task.js --task-id <task-id> --assigned-agent-id <agent-id>
```

### Close a task

```bash
node skills/mission-control/close-task.js --task-id <task-id>
```

### Add a comment to a task

```bash
node skills/mission-control/add-comment.js --task-id <task-id> --message "Analysis complete. See attached output."
```

## API Reference

Full API operation list: `./mission-control-operations.txt`
Full OpenAPI schema: `./openapi.json`

Use `BASE_URL`, `AUTH_TOKEN`, and `BOARD_ID` from your `TOOLS.md`.
All agent-scoped requests require header: `X-Agent-Token: $AUTH_TOKEN`

## Pre-Flight Checks (Every Heartbeat)

1. Confirm `BASE_URL`, `AUTH_TOKEN`, and `BOARD_ID` from `TOOLS.md` match this workspace.
2. Verify API access:
   - `GET $BASE_URL/healthz`
   - `GET $BASE_URL/api/v1/agent/boards`

## Notes

- Rate limit: ~3 requests/second average
- Scripts make exactly one API call each; no internal retries
- If any required env var is missing, the script exits immediately with a clear error message
