#!/usr/bin/env node
'use strict';
/**
 * Minimal SSE live-reload dev server for html-book-bundler.
 *
 * Usage:
 *   1. Build the book with --dev flag:
 *        node bundle.cjs --input ./chapters --output book.html --dev
 *   2. Start this server:
 *        node dev_server.cjs book.html [port]
 *   3. Open http://localhost:3000 — the page reloads on every file save.
 *
 * The injected EventSource(/events) client (from --dev) connects here.
 * Zero dependencies — uses only Node.js stdlib.
 */
const http = require('http');
const fs   = require('fs');
const path = require('path');

const filePath = path.resolve(process.argv[2] || 'book.html');
const PORT     = parseInt(process.argv[3] || process.env.PORT || '3000', 10);

if (!fs.existsSync(filePath)) {
  console.error(`Error: file not found: ${filePath}`);
  console.error(`Usage: node dev_server.cjs <book.html> [port]`);
  process.exit(1);
}

let clients  = [];
let lastMtime = fs.statSync(filePath).mtimeMs;

// ── Watch for file changes ────────────────────────────────────────────────────
fs.watch(filePath, () => {
  try {
    const mtime = fs.statSync(filePath).mtimeMs;
    if (mtime !== lastMtime) {
      lastMtime = mtime;
      console.log(`[dev] ${path.basename(filePath)} changed — reloading ${clients.length} client(s)`);
      clients.forEach(res => {
        try { res.write('data: reload\n\n'); } catch(e) {}
      });
    }
  } catch (e) { /* file may be mid-write; ignore */ }
});

// ── HTTP server ───────────────────────────────────────────────────────────────
const server = http.createServer((req, res) => {
  if (req.url === '/events') {
    // Server-Sent Events endpoint — the --dev injected script connects here
    res.writeHead(200, {
      'Content-Type':  'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection':    'keep-alive',
      'Access-Control-Allow-Origin': '*',
    });
    clients.push(res);
    // Keep-alive ping every 25s (prevents proxy timeouts)
    const keepAlive = setInterval(() => {
      try { res.write(': ping\n\n'); } catch(e) { clearInterval(keepAlive); }
    }, 25_000);
    req.on('close', () => {
      clearInterval(keepAlive);
      clients = clients.filter(c => c !== res);
    });
    return;
  }

  // Serve the bundled HTML file for all other requests
  try {
    const html = fs.readFileSync(filePath, 'utf8');
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
    res.end(html);
  } catch(e) {
    res.writeHead(500);
    res.end('Error reading file');
  }
});

server.listen(PORT, '127.0.0.1', () => {
  console.log(`[dev] Serving  : ${filePath}`);
  console.log(`[dev] Open     : http://localhost:${PORT}`);
  console.log(`[dev] Watching : changes auto-reload the browser (Ctrl+C to stop)`);
});
