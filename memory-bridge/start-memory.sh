#!/usr/bin/env sh
set -e

exec supergateway \
  --stdio "node /app/dist/index.js" \
  --outputTransport streamableHttp \
  --protocolVersion 2024-11-05 \
  --port 8000 \
  --healthEndpoint /healthz
