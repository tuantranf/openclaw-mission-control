#!/usr/bin/env node
// Usage: node message-lead.js --board-id <id> --kind question|handoff --content <message> [--correlation-id <id>]
// Env:   BASE_URL, AUTH_TOKEN

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

  const args = parseArgs();

  if (!args['board-id']) {
    process.stderr.write('[ERROR] Missing required argument: --board-id\n');
    process.exit(1);
  }
  if (!args['kind']) {
    process.stderr.write('[ERROR] Missing required argument: --kind (question|handoff)\n');
    process.exit(1);
  }
  if (args['kind'] !== 'question' && args['kind'] !== 'handoff') {
    process.stderr.write('[ERROR] --kind must be "question" or "handoff"\n');
    process.exit(1);
  }
  if (!args['content']) {
    process.stderr.write('[ERROR] Missing required argument: --content\n');
    process.exit(1);
  }

  const body = { kind: args['kind'], content: args['content'] };
  if (args['correlation-id']) body.correlation_id = args['correlation-id'];

  const res = await fetch(`${BASE_URL}/api/v1/agent/gateway/boards/${args['board-id']}/lead/message`, {
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
