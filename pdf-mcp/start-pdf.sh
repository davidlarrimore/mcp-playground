#!/usr/bin/env sh
set -e

exec supergateway \
  --stdio "python -m pdf_mcp.server" \
  --outputTransport streamableHttp \
  --protocolVersion 2024-11-05 \
  --port 8000 \
  --healthEndpoint /healthz
