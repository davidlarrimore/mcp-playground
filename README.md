# MCP Lab - Dockerized Demo Stack

This repo spins up the Part 2 demo services from `demo-tech-mapping.md` on a single Docker network with MailHog for SMTP capture and a custom Email service. Open WebUI and LiteLLM run in their own project; they should join the same Docker network and call these services by container name.

## What’s inside
- MailHog (SMTP sink + web UI) on host ports `2005` (UI) / `2025` (SMTP)
- Reference MCP servers (container names): `time-mcp`, `filesystem-mcp`, `memory-mcp`
- Custom Email HTTP service: `email-mcp` (POST `/send`)
- MCPO OpenAPI proxy that wraps the MCP servers
- Shared Docker network: `mcp-net`
- Shared data mount for attachments and filesystem demo data: `./demo-data`

## Quickstart
1) Copy env defaults and tweak ports/paths if needed:
```bash
cp .env.example .env
```

2) Build and start the stack (bridging stdio→HTTP images are built locally):
```bash
make up
```

3) Tail logs:
```bash
make logs
```

4) Visit MailHog UI: `http://localhost:2005`

5) Stop everything:
```bash
make down
```

6) Full teardown (containers + volumes):
```bash
make nuke
```

## Service endpoints (dev profile)
- Time MCP: `http://localhost:${TIME_MCP_PORT:-2001}`
- Filesystem MCP: `http://localhost:${FILESYSTEM_MCP_PORT:-2002}`
- Memory MCP: `http://localhost:${MEMORY_MCP_PORT:-2003}`
- Email service: `http://localhost:${EMAIL_MCP_PORT:-2004}`
- MailHog UI: `http://localhost:${MAILHOG_WEB_PORT:-2005}`
- MCPO OpenAPI proxy: `http://localhost:${MCPO_PORT:-2010}`

> The reference MCP images ship as stdio servers. Compose builds lightweight wrappers (time-bridge, filesystem-bridge, memory-bridge) using `supergateway` to expose Streamable HTTP endpoints.

## Custom Email service (now MCP-aware)
- Container: `email-mcp`
- MCP endpoint: `http://localhost:${EMAIL_MCP_PORT:-2004}/mcp` (Streamable HTTP via supergateway)
- HTTP convenience API (unchanged): `POST /send`
- Health: `GET /healthz`
- Env: `SMTP_HOST`, `SMTP_PORT`, `SMTP_FROM_DEFAULT`, `ATTACH_ROOT`, `LOG_LEVEL`
- Volumes: mounts `./demo-data` read-only at `/attachments` so you can attach scenario files.

Example request:
```bash
curl -X POST http://localhost:2004/send \
  -H "Content-Type: application/json" \
  -d '{
    "to": ["ops@example.com"],
    "subject": "Week 8 invite",
    "body_text": "See you Thursday at noon ET.",
    "attachments": [{"path": "CourseOutlineWeek8.pdf", "filename": "Week8Outline.pdf"}]
  }'
```

## Local (venv) email service
Run the email service without Docker (uses `.env` if present):
```bash
make email-local
```
This creates `.venv`, installs `email-mcp/requirements.txt`, and runs `python -m email_mcp.server`. Stop with:
```bash
make email-local-stop
```

## Filesystem + attachments
- Place demo documents under `demo-data/`. Files are available inside containers at `${FILESYSTEM_ROOT}` (default `/demo-data`) and the email service at `${ATTACH_ROOT}` (default `/attachments`).
- Filesystem MCP is invoked with the allowed path set to `${FILESYSTEM_ROOT}` to avoid escaping the demo directory.

## Make targets
- `make up` – start all services
- `make down` – stop services
- `make logs` – follow container logs
- `make ps` – view container status
- `make rebuild` – rebuild images (pull base layers)
- `make nuke` – remove containers and volumes (blows away memory data)
- `make email-local` – run email service in local venv
- `make email-local-stop` – stop the local email process

## MCPO OpenAPI proxy (wraps all MCP servers)
- Container: `mcpo`
- Base URL: `http://localhost:${MCPO_PORT:-2010}`
- Routes (per tool): `/time`, `/filesystem`, `/memory`, `/email` with generated OpenAPI docs at `/<tool>/docs` (e.g., `http://localhost:2010/time/docs`) and schemas at `/<tool>/openapi.json`.
- How it connects: proxies the Streamable HTTP endpoints of `time-mcp`, `filesystem-mcp`, `memory-mcp`, and `email-mcp` on the same Docker network.
- Open WebUI integration: add an **OpenAPI** server pointing to `http://localhost:2010/time/openapi.json` (or `http://mcpo:8000/time/openapi.json` if Open WebUI runs on `mcp-net`). Repeat per tool if you want individual OpenAPI servers.

## Notes for Open WebUI wiring
- Ensure Open WebUI joins `mcp-net` or can reach `localhost` on the mapped ports.
- Add tool servers in Open WebUI pointing at the hostnames/ports above.
## Open WebUI setup
- Network: either (a) run Open WebUI on the host and use localhost ports above, or (b) attach its container to `mcp-net` so it can resolve `time-mcp`, `filesystem-mcp`, `memory-mcp`, `email-mcp` by name. Example: `docker network connect mcp-net <openwebui_container>`.
- In Open WebUI → Settings → Tools (External Tools) → Add Tool Server:
  - Type: `MCP (Streamable HTTP)`
  - Name/URL pairs:
    - `time` → `http://time-mcp:8000/mcp` (or `http://host.docker.internal:2001/mcp`)
    - `filesystem` → `http://filesystem-mcp:8000/mcp` (or `http://host.docker.internal:2002/mcp`)
    - `memory` → `http://memory-mcp:8000/mcp` (or `http://host.docker.internal:2003/mcp`)
    - `email` → `http://email-mcp:8000/mcp` (or `http://host.docker.internal:2004/mcp`)
- Click “Test connection” for each; you should see the tool list returned.
- To use the OpenAPI proxy instead, add OpenAPI servers pointing at `http://localhost:2010/<tool>/openapi.json` (or `http://mcpo:8000/<tool>/openapi.json` on `mcp-net`), where `<tool>` is `time`, `filesystem`, `memory`, or `email`.

### Open WebUI connection fields (per tool)
- Type: `MCP Streamable HTTP`
- URL:
  - If Open WebUI is on the host: `http://localhost:<port>/mcp` (2001/2002/2003/2004)
  - If Open WebUI is in Docker but **not** on `mcp-net`: `http://host.docker.internal:<port>/mcp`
  - If Open WebUI is on `mcp-net`: `http://time-mcp:8000/mcp`, `http://filesystem-mcp:8000/mcp`, `http://memory-mcp:8000/mcp`, `http://email-mcp:8000/mcp`
- Auth: None (leave blank)
- Headers: leave empty
- ID: optional (Open WebUI will generate)
- Name: any short name you prefer (e.g., `time`, `filesystem`, `memory`, `email`)
- Description: optional
- Function Name Filter List: leave empty unless you need to hide functions

## Quick verification checks
Run these after `make up`:
- Health endpoints:
  ```bash
  curl http://localhost:2001/healthz
  curl http://localhost:2002/healthz
curl http://localhost:2003/healthz
curl http://localhost:2004/healthz
```
- MCPO OpenAPI docs (time tool):
  ```bash
  curl -I http://localhost:2010/time/docs
  ```
- Filesystem container sees demo data:
  ```bash
  docker compose --env-file .env exec filesystem-mcp ls /demo-data
  ```
- Memory persistence path is mounted:
  ```bash
  docker compose --env-file .env exec memory-mcp ls /data
  ```
- Email send path (hits MailHog):
  ```bash
  curl -X POST http://localhost:2004/send \
    -H "Content-Type: application/json" \
    -d '{"to":["ops@example.com"],"subject":"Ping","body_text":"hello"}'
  ```
  Then open MailHog UI (`http://localhost:2005`) and confirm the message appears.

## Debugging tips
- Check service logs: `docker compose --env-file .env logs <service> -f`
- Verify MailHog SMTP connectivity from the email container:
  ```bash
  docker compose --env-file .env exec email-mcp nc -z mailhog 1025
  ```
- Validate attach path: container should see files at `${ATTACH_ROOT}`; use `docker compose exec email-mcp ls /attachments`.
