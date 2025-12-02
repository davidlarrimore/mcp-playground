#!/usr/bin/env sh
set -e

ROOT="${FILESYSTEM_ROOT:-/docs}"
export FS_BASE_DIRECTORY="${FS_BASE_DIRECTORY:-$ROOT}"
SERVER_BIN="$(npm root -g)/@cyanheads/filesystem-mcp-server/dist/index.js"

exec supergateway \
  --stdio "node ${SERVER_BIN}" \
  --outputTransport streamableHttp \
  --protocolVersion 2024-11-05 \
  --port 8000 \
  --healthEndpoint /healthz
