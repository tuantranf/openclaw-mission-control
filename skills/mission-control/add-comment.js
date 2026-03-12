#!/usr/bin/env node
// Usage: node add-comment.js --task-id <id> --message <message>
// Env:   BASE_URL, AUTH_TOKEN, BOARD_ID

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
  const BOARD_ID = requireEnv('BOARD_ID');

  const args = parseArgs();

  if (!args['task-id']) {
    process.stderr.write('[ERROR] Missing required argument: --task-id\n');
    process.exit(1);
  }
  if (!args['message']) {
    process.stderr.write('[ERROR] Missing required argument: --message\n');
    process.exit(1);
  }

  const res = await fetch(`${BASE_URL}/api/v1/agent/boards/${BOARD_ID}/tasks/${args['task-id']}/comments`, {
    method: 'POST',
    headers: {
      'X-Agent-Token': AUTH_TOKEN,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ message: args['message'] }),
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
