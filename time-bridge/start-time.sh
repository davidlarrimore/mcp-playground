#!/usr/bin/env sh
set -e

LOCAL_TZ="${LOCAL_TIMEZONE:-America/New_York}"

exec supergateway \
  --stdio "/app/.venv/bin/mcp-server-time --local-timezone ${LOCAL_TZ}" \
  --outputTransport streamableHttp \
  --protocolVersion 2024-11-05 \
  --port 8000 \
  --healthEndpoint /healthz
