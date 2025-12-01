# MCP Lab - Dockerized Demo Stack

This repo spins up the Part 2 demo services from `demo-tech-mapping.md` on a single Docker network with MailHog for SMTP capture and a custom Email service. Open WebUI and LiteLLM run in their own project; they should join the same Docker network and call these services by container name.

## What’s inside
- MailHog (SMTP sink + web UI) on host ports `2005` (UI) / `2025` (SMTP)
- Reference MCP servers (container names): `time-mcp`, `filesystem-mcp`, `memory-mcp`
- Custom Email HTTP service: `email-mcp` (POST `/send`)
- Shared Docker network: `mcp-net`
- Shared data mount for attachments and filesystem demo data: `./demo-data`

## Quickstart
1) Copy env defaults and tweak ports/paths if needed:
```bash
cp .env.example .env
```

2) Start the stack:
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

> The reference MCP images currently ship as stdio servers. Exposing them on ports allows you to front them with your preferred HTTP adapter; adjust commands if you use an updated HTTP-capable tag.

## Custom Email service
- Container: `email-mcp`
- HTTP: `POST /send`
- Health: `GET /healthz`
- Env: `SMTP_HOST`, `SMTP_PORT`, `SMTP_FROM_DEFAULT`, `ATTACH_ROOT`, `LOG_LEVEL`
- Volumes: mounts `./demo-data` read-only at `/attachments` so you can attach scenario files.

Example request:
```bash
curl -X POST http://localhost:2004/send \
  -H "Content-Type: application/json" \
  -d '{
    "to": ["ops@example.test"],
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

## Notes for Open WebUI wiring
- Ensure Open WebUI joins `mcp-net` or can reach `localhost` on the mapped ports.
- Add tool servers in Open WebUI pointing at the hostnames/ports above.
- LiteLLM continues to run on port `7777` (external to this compose file).

## Debugging tips
- Check service logs: `docker compose --env-file .env logs <service> -f`
- Verify MailHog SMTP connectivity from the email container:
  ```bash
  docker compose --env-file .env exec email-mcp nc -z mailhog 1025
  ```
- Validate attach path: container should see files at `${ATTACH_ROOT}`; use `docker compose exec email-mcp ls /attachments`.
