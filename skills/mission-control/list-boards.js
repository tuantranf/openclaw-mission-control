#!/usr/bin/env node
// Usage: node list-boards.js
// Env:   BASE_URL, AUTH_TOKEN

function requireEnv(name) {
  const val = process.env[name];
  if (!val) {
    process.stderr.write(`[ERROR] Missing env var: ${name}\n`);
    process.exit(1);
  }
  return val;
}

async function main() {
  const BASE_URL = requireEnv('BASE_URL');
  const AUTH_TOKEN = requireEnv('AUTH_TOKEN');

  const res = await fetch(`${BASE_URL}/api/v1/agent/boards`, {
    method: 'GET',
    headers: {
      'X-Agent-Token': AUTH_TOKEN,
      'Content-Type': 'application/json',
    },
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
