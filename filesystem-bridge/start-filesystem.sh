#!/usr/bin/env sh
set -e

ROOT="${FILESYSTEM_ROOT:-/demo-data}"

exec supergateway \
  --stdio "node /app/dist/index.js ${ROOT}" \
  --outputTransport streamableHttp \
  --protocolVersion 2024-11-05 \
  --port 8000 \
  --healthEndpoint /healthz
