#!/usr/bin/env node
// Usage: node heartbeat.js [--status healthy|working|idle]
// Env:   BASE_URL, AUTH_TOKEN, AGENT_NAME — required
//        BOARD_ID — optional (omit for main/non-board-scoped agents)

function requireEnv(name) {
  const val = process.env[name];
  if (!val) {
    process.stderr.write(`[ERROR] Missing env var: ${name}\n`);
    process.exit(1);
  }
  return val;
}

function parseArgs() {
  const args = {};
  const argv = process.argv.slice(2);
  for (let i = 0; i < argv.length; i += 2) {
    const key = argv[i].replace(/^--/, '');
    args[key] = argv[i + 1];
  }
  return args;
}

async function main() {
  const BASE_URL = requireEnv('BASE_URL');
  const AUTH_TOKEN = requireEnv('AUTH_TOKEN');
  const AGENT_NAME = requireEnv('AGENT_NAME');
  const BOARD_ID = process.env['BOARD_ID'];  // optional for main (non-board-scoped) agents

  const args = parseArgs();
  const status = args['status'] || 'healthy';

  const body = { status, name: AGENT_NAME };
  if (BOARD_ID) body.board_id = BOARD_ID;

  const res = await fetch(`${BASE_URL}/api/v1/agent/heartbeat`, {
    method: 'POST',
    headers: {
      'X-Agent-Token': AUTH_TOKEN,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const text = await res.text();
    process.stderr.write(`[ERROR] HTTP ${res.status}: ${text}\n`);
    process.exit(1);
  }

  const json = await res.json();
  process.stdout.write(JSON.stringify(json, null, 2) + '\n');
}

main().catch(err => {
  process.stderr.write(`[ERROR] ${err.message}\n`);
  process.exit(1);
});
