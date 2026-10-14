#!/usr/bin/env node
'use strict';

// universal stdio driver for the playwright MCP server: handshake once, send
// each command, await the response by matching id (no sleep races), print a
// readable per-call summary. see mcp-call.sh for the entrypoint.

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const readline = require('readline');

const SKILL_DIR = __dirname;
const WRAPPER = path.join(SKILL_DIR, 'playwright-mcp.sh');
const REQ_TIMEOUT = parseInt(process.env.MCP_TIMEOUT_MS || '60000', 10);
const TRUNCATE = 500;

function printHelp() {
  console.log(`mcp-call.sh - drive the playwright MCP server over stdio

usage:
  mcp-call.sh [options] '<command>' ['<command>' ...]
  mcp-call.sh [options] --file commands.txt
  echo '<command>' | mcp-call.sh [options]

command forms (one per arg / per line):
  browser_navigate {"url":"https://opera.com"}   tool + JSON arguments
  browser_snapshot                               tool with no arguments
  {"method":"tools/list","params":{}}            full JSON-RPC passthrough
  # lines starting with # are ignored

options:
  --full     print full text content (default truncates to ${TRUNCATE} chars)
  --json     print raw JSON-RPC responses
  --debug    stream server stderr
  --file P   read commands from file P (one per line)
  -h         this help

env:
  MCP_TIMEOUT_MS   per-request timeout (default ${REQ_TIMEOUT})`);
}

function parseArgs(argv) {
  const opts = { full: false, json: false, debug: false, file: null, help: false, commands: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--full') opts.full = true;
    else if (a === '--json') opts.json = true;
    else if (a === '--debug') opts.debug = true;
    else if (a === '--file') opts.file = argv[++i];
    else if (a === '-h' || a === '--help') opts.help = true;
    else opts.commands.push(a);
  }
  return opts;
}

function readCommandLines(opts) {
  let lines = [];
  if (opts.file) lines = fs.readFileSync(opts.file, 'utf8').split('\n');
  else if (opts.commands.length) lines = opts.commands;
  else if (!process.stdin.isTTY) lines = fs.readFileSync(0, 'utf8').split('\n');
  return lines.map((l) => l.trim()).filter((l) => l && !l.startsWith('#'));
}

function toRequest(line, id) {
  const t = line.trim();
  if (t.startsWith('{')) {
    const obj = JSON.parse(t);
    if (!obj.jsonrpc) obj.jsonrpc = '2.0';
    if (obj.id == null) obj.id = id;
    return obj;
  }
  const sp = t.indexOf(' ');
  const tool = sp === -1 ? t : t.slice(0, sp);
  const argsRaw = sp === -1 ? '{}' : t.slice(sp + 1).trim() || '{}';
  let args;
  try {
    args = JSON.parse(argsRaw);
  } catch (e) {
    throw new Error(`bad args JSON for ${tool}: ${argsRaw}`);
  }
  return { jsonrpc: '2.0', id, method: 'tools/call', params: { name: tool, arguments: args } };
}

function summarize(resp, opts) {
  if (opts.json) return JSON.stringify(resp);
  if (resp.error) return `ERROR  ${resp.error.message || JSON.stringify(resp.error)}`;
  const r = resp.result || {};
  const head = r.isError ? 'ERROR' : 'OK';
  const parts = (r.content || []).map((c) => (c.text != null ? c.text : `[${c.type}]`));
  let text = parts.join('\n');
  if (!opts.full && text.length > TRUNCATE) {
    text = `${text.slice(0, TRUNCATE)} … (+${text.length - TRUNCATE} chars, use --full)`;
  }
  return text ? `${head}\n${text}` : head;
}

function indent(s) {
  return s
    .split('\n')
    .map((l) => `  ${l}`)
    .join('\n');
}

async function main() {
  const opts = parseArgs(process.argv.slice(2));
  if (opts.help) {
    printHelp();
    return;
  }
  const cmds = readCommandLines(opts);
  if (!cmds.length) {
    printHelp();
    process.exit(1);
  }

  const child = spawn(WRAPPER, [], { stdio: ['pipe', 'pipe', 'pipe'] });
  const pending = new Map();
  let stderr = '';

  readline.createInterface({ input: child.stdout }).on('line', (line) => {
    const t = line.trim();
    if (!t.startsWith('{')) return;
    let obj;
    try {
      obj = JSON.parse(t);
    } catch {
      return;
    }
    if (obj.id != null && pending.has(obj.id)) {
      const { resolve } = pending.get(obj.id);
      pending.delete(obj.id);
      resolve(obj);
    }
  });
  child.stderr.on('data', (d) => {
    stderr += d;
    if (opts.debug) process.stderr.write(d);
  });
  child.on('exit', () => {
    for (const { reject } of pending.values()) reject(new Error('server exited'));
  });

  function send(req) {
    child.stdin.write(`${JSON.stringify(req)}\n`);
    return new Promise((resolve, reject) => {
      const to = setTimeout(() => {
        pending.delete(req.id);
        reject(new Error(`timeout after ${REQ_TIMEOUT}ms for id ${req.id}`));
      }, REQ_TIMEOUT);
      pending.set(req.id, {
        resolve: (v) => {
          clearTimeout(to);
          resolve(v);
        },
        reject: (e) => {
          clearTimeout(to);
          reject(e);
        },
      });
    });
  }

  await send({
    jsonrpc: '2.0',
    id: 1,
    method: 'initialize',
    params: { protocolVersion: '2024-11-05', capabilities: {}, clientInfo: { name: 'mcp-call', version: '1.0' } },
  });
  child.stdin.write(`${JSON.stringify({ jsonrpc: '2.0', method: 'notifications/initialized' })}\n`);

  let id = 2;
  let exitCode = 0;
  for (const line of cmds) {
    let req;
    try {
      req = toRequest(line, id++);
    } catch (e) {
      console.log(`→ ${line}\n${indent(`PARSE-ERROR  ${e.message}`)}\n`);
      exitCode = 1;
      continue;
    }
    const label = req.method === 'tools/call' ? req.params.name : req.method;
    process.stdout.write(`→ [${req.id}] ${label}\n`);
    try {
      const resp = await send(req);
      if ((resp.result && resp.result.isError) || resp.error) exitCode = 1;
      console.log(`${indent(summarize(resp, opts))}\n`);
    } catch (e) {
      console.log(indent(`ERROR  ${e.message}`));
      if (stderr && !opts.debug) console.log(indent(`--- server stderr ---\n${stderr}`));
      exitCode = 1;
      break;
    }
  }

  try {
    child.stdin.end();
  } catch {}
  child.kill();
  process.exit(exitCode);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
