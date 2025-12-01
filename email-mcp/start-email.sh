#!/usr/bin/env sh
set -e

exec supergateway \
  --stdio "python -m email_mcp.mcp_server" \
  --outputTransport streamableHttp \
  --protocolVersion 2024-11-05 \
  --port 8000 \
  --healthEndpoint /healthz
