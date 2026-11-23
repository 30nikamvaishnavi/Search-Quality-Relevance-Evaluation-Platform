import { spawn } from 'node:child_process';
import fs from 'node:fs';
import http from 'node:http';
import net from 'node:net';
import path from 'node:path';

const PORT = 3000;
const STREAMLIT_HOST = '127.0.0.1';
const STREAMLIT_PORT = 8501;

const venvStreamlit = path.resolve(process.cwd(), '.venv/bin/streamlit');
const streamlitCmd = fs.existsSync(venvStreamlit) ? venvStreamlit : 'streamlit';

const streamlitProc = spawn(
  streamlitCmd,
  [
    'run',
    'app.py',
    `--server.port=${STREAMLIT_PORT}`,
    `--server.address=${STREAMLIT_HOST}`,
    '--server.headless=true',
    '--server.enableCORS=false',
    '--server.enableXsrfProtection=false',
  ],
  {
    stdio: 'inherit',
    env: process.env,
  },
);

streamlitProc.on('exit', (code) => {
  console.error(`Streamlit exited with code ${code ?? 'unknown'}`);
  process.exit(code ?? 1);
});

const server = http.createServer((req, res) => {
  const proxyReq = http.request(
    {
      hostname: STREAMLIT_HOST,
      port: STREAMLIT_PORT,
      path: req.url ?? '/',
      method: req.method,
      headers: {
        ...req.headers,
        host: `${STREAMLIT_HOST}:${STREAMLIT_PORT}`,
      },
    },
    (proxyRes) => {
      res.writeHead(proxyRes.statusCode ?? 200, proxyRes.headers);
      proxyRes.pipe(res);
    },
  );

  proxyReq.on('error', () => {
    if (!res.headersSent) {
      res.writeHead(503, {
        'Content-Type': 'text/html; charset=utf-8',
        Refresh: '2',
      });
      res.end(
        '<!doctype html><html><body style="font-family:sans-serif;padding:2rem;">' +
          '<h2>Starting SearchEval Streamlit Server...</h2>' +
          '<p>Loading Python evaluation engine and dashboard. This page refreshes automatically.</p>' +
          '</body></html>',
      );
    }
  });

  req.pipe(proxyReq);
});

server.on('upgrade', (req, clientSocket, head) => {
  const upstream = net.connect(STREAMLIT_PORT, STREAMLIT_HOST, () => {
    const headerLines = [`${req.method ?? 'GET'} ${req.url ?? '/'} HTTP/1.1`];
    for (let i = 0; i < req.rawHeaders.length; i += 2) {
      const name = req.rawHeaders[i];
      const value = req.rawHeaders[i + 1];
      if (name.toLowerCase() === 'host') {
        headerLines.push(`Host: ${STREAMLIT_HOST}:${STREAMLIT_PORT}`);
      } else {
        headerLines.push(`${name}: ${value}`);
      }
    }
    upstream.write(`${headerLines.join('\r\n')}\r\n\r\n`);
    if (head.length > 0) {
      upstream.write(head);
    }
    upstream.pipe(clientSocket);
    clientSocket.pipe(upstream);
  });

  upstream.on('error', () => {
    clientSocket.destroy();
  });
  clientSocket.on('error', () => {
    upstream.destroy();
  });
});

function shutdown() {
  streamlitProc.kill('SIGTERM');
  server.close(() => process.exit(0));
}

process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);

server.listen(PORT, '0.0.0.0', () => {
  console.log(`SearchEval proxy listening on http://0.0.0.0:${PORT} -> Streamlit ${STREAMLIT_HOST}:${STREAMLIT_PORT}`);
});
