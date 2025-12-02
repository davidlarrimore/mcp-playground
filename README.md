# MCP Lab - Dockerized Demo Stack

This repo provides a complete MCP (Model Context Protocol) demonstration stack with 8 professional services running on Docker. It includes core utilities (time, filesystem, memory, email) plus advanced document generation capabilities (Excel, Word, PDF, analytics).

**✨ New:** Professional document generation services with Excel workbooks, Word reports, PDF creation, and data analytics with chart generation!

## Features

**Core Services (4):**
- ⏰ Time & timezone operations
- 📁 Filesystem operations (read/write/manage files)
- 🧠 Persistent memory storage
- 📧 Email with attachments via MailHog

**Document Generation (4):**
- 📊 Excel - Create workbooks with charts and formatting
- 📝 Word - Generate professional reports with tables
- 📄 PDF - Convert HTML to high-quality PDFs
- 📈 Analytics - Merge data, calculate stats, create charts

**Integration:**
- 🔌 MCPO OpenAPI proxy for unified access
- 🐳 Full Docker Compose setup
- 🌐 Open WebUI compatible (MCP Streamable HTTP)
- 📂 Shared workspace across all services

## What's inside
- MailHog (SMTP sink + web UI) on host ports `2005` (UI) / `2025` (SMTP)
- Reference MCP servers (container names): `time-mcp`, `filesystem-mcp`, `memory-mcp`
- Custom Email HTTP service: `email-mcp` (POST `/send`)
- **Document Generation Services**: `excel-mcp`, `word-mcp`, `pdf-mcp`, `analytics-mcp`
- MCPO OpenAPI proxy that wraps all MCP servers
- FastMCP 2.0 powering the custom MCP interfaces (bridged to Streamable HTTP)
- Shared Docker network: `mcp-net`
- Shared data mount for attachments and filesystem files: `./docs`

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
- Email MCP: `http://localhost:${EMAIL_MCP_PORT:-2004}`
- MailHog UI: `http://localhost:${MAILHOG_WEB_PORT:-2005}`
- **Excel MCP**: `http://localhost:${EXCEL_MCP_PORT:-2006}`
- **Word MCP**: `http://localhost:${WORD_MCP_PORT:-2007}`
- **PDF MCP**: `http://localhost:${PDF_MCP_PORT:-2008}`
- **Analytics MCP**: `http://localhost:${ANALYTICS_MCP_PORT:-2009}`
- MCPO OpenAPI proxy: `http://localhost:${MCPO_PORT:-2010}`

> The reference MCP images ship as stdio servers. Compose builds lightweight wrappers (time-bridge, filesystem-bridge, memory-bridge) using `supergateway` to expose Streamable HTTP endpoints.

## Custom Email service (now MCP-aware)
- Built on FastMCP 2.0 (stdio tools bridged to Streamable HTTP via `supergateway` at `/mcp`)
- Container: `email-mcp`
- MCP endpoint: `http://localhost:${EMAIL_MCP_PORT:-2004}/mcp` (Streamable HTTP via supergateway)
- HTTP convenience API (unchanged): `POST /send`
- Health: `GET /healthz`
- Env: `SMTP_HOST`, `SMTP_PORT`, `SMTP_FROM_DEFAULT`, `ATTACH_ROOT`, `LOG_LEVEL`
- Volumes: mounts `./docs` read-only at `/attachments` so you can attach scenario files.
- Attachments: pass objects with a `path` (relative to `/attachments`); plain strings work too, but must resolve under `/attachments` or you’ll get a 400. Example `{"path": "bp_crossings_central.xlsx"}`.

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

## Document Generation Services

Four new MCP services provide professional document creation and data analysis capabilities. All services share the `./docs` workspace and are built on FastMCP 2.0.

### Excel MCP (`excel-mcp`)
- Container: `excel-mcp`
- Port: `${EXCEL_MCP_PORT:-2006}`
- MCP endpoint: `http://localhost:2006/mcp`
- Health: `GET /healthz`
- **Tools:**
  - `save_uploaded_file` - Save uploaded files to workspace (base64)
  - `create_excel_workbook` - Create Excel files with formatted sheets, charts (bar/line), and auto-sizing

### Word MCP (`word-mcp`)
- Container: `word-mcp`
- Port: `${WORD_MCP_PORT:-2007}`
- MCP endpoint: `http://localhost:2007/mcp`
- Health: `GET /healthz`
- **Tools:**
  - `save_uploaded_file` - Save uploaded files to workspace (base64)
  - `create_word_report` - Create Word documents with titles, sections, tables, bullet points, and formatting

### PDF MCP (`pdf-mcp`)
- Container: `pdf-mcp`
- Port: `${PDF_MCP_PORT:-2008}`
- MCP endpoint: `http://localhost:2008/mcp`
- Health: `GET /healthz`
- **Tools:**
  - `save_uploaded_file` - Save uploaded files to workspace (base64)
  - `create_pdf_from_html` - Convert HTML (string or file) to PDF with optional CSS styling

### Analytics MCP (`analytics-mcp`)
- Container: `analytics-mcp`
- Port: `${ANALYTICS_MCP_PORT:-2009}`
- MCP endpoint: `http://localhost:2009/mcp`
- Health: `GET /healthz`
- **Tools:**
  - `save_uploaded_file` - Save uploaded files to workspace (base64)
  - `list_data_files` - List available CSV/Excel files with optional glob patterns
  - `merge_excel_files` - Merge multiple CSV/Excel files into one dataset
  - `calculate_summary_stats` - Calculate statistics with optional grouping
  - `generate_chart` - Create bar, line, or pie charts from data

### Shared Workspace
- All document services mount `./docs` as their workspace at `/workspace`
- Files created by one service are immediately accessible to all others
- **Important:** When using file paths in tool calls, do NOT include `docs/` prefix (e.g., use `"report.xlsx"` not `"docs/report.xlsx"`)

### Working with Uploaded Files
When users upload files via Open WebUI chat, use the `save_uploaded_file` tool (available in all 4 services) to save them to the workspace:

```json
{
  "filename": "data.xlsx",
  "content_base64": "<base64-encoded file content>"
}
```

See `docs/QUICK_START.md` and `docs/MCP_USAGE_GUIDE.md` for detailed usage examples.

## Local (venv) email service
Run the email service without Docker (uses `.env` if present). Requires Python >=3.10 for FastMCP 2.x; set `PYTHON_BIN` if you need to point at a specific interpreter:
```bash
make email-local
```
This creates `.venv`, installs `email-mcp/requirements.txt`, and runs `python -m email_mcp.server`. Stop with:
```bash
make email-local-stop
```

## Filesystem + attachments
- Place documents under `docs/`. Files are available inside containers at `${FILESYSTEM_ROOT}` (default `/docs`) and the email service at `${ATTACH_ROOT}` (default `/attachments`).
- Filesystem MCP now uses the upstream [`@cyanheads/filesystem-mcp-server`](https://github.com/cyanheads/filesystem-mcp-server) wrapped with `supergateway`, restricted to `${FILESYSTEM_ROOT}` to avoid escaping the host directory.
- Core tools (see upstream docs for full schemas): `list_files`, `read_file`, `write_file`, `update_file`, `delete_file`, `delete_directory`, `create_directory`, `move_path`, `copy_path`, plus `set_filesystem_default` for session-relative paths. `write_file` overwrites or creates text files under the root; combine with `copy_path` if you need to duplicate existing binaries.
- The container initializes the default filesystem path to `${FILESYSTEM_ROOT}`, so relative paths work out of the box through MCPO/Open WebUI.

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
- Routes (per tool): `/time`, `/filesystem`, `/memory`, `/email`, `/excel`, `/word`, `/pdf`, `/analytics` with generated OpenAPI docs at `/<tool>/docs` (e.g., `http://localhost:2010/analytics/docs`) and schemas at `/<tool>/openapi.json`.
- How it connects: proxies the Streamable HTTP endpoints of all MCP services on the same Docker network.
- **All 8 MCP services accessible through MCPO:**
  - Core services: `time-mcp`, `filesystem-mcp`, `memory-mcp`, `email-mcp`
  - Document services: `excel-mcp`, `word-mcp`, `pdf-mcp`, `analytics-mcp`
- Open WebUI integration: add an **OpenAPI** server pointing to `http://localhost:2010/<tool>/openapi.json` (or `http://mcpo:8000/<tool>/openapi.json` if Open WebUI runs on `mcp-net`). Repeat per tool if you want individual OpenAPI servers, or use MCP Streamable HTTP type to add all at once.

## Notes for Open WebUI wiring
- Ensure Open WebUI joins `mcp-net` or can reach `localhost` on the mapped ports.
- Add tool servers in Open WebUI pointing at the hostnames/ports above.
## Open WebUI setup
- Network: either (a) run Open WebUI on the host and use localhost ports above, or (b) attach its container to `mcp-net` so it can resolve service names. Example: `docker network connect mcp-net <openwebui_container>`.
- In Open WebUI → Settings → Tools (External Tools) → Add Tool Server:
  - Type: `MCP (Streamable HTTP)`
  - **Option 1 - Individual Services** (Name/URL pairs):
    - `time` → `http://time-mcp:8000/mcp` (or `http://host.docker.internal:2001/mcp`)
    - `filesystem` → `http://filesystem-mcp:8000/mcp` (or `http://host.docker.internal:2002/mcp`)
    - `memory` → `http://memory-mcp:8000/mcp` (or `http://host.docker.internal:2003/mcp`)
    - `email` → `http://email-mcp:8000/mcp` (or `http://host.docker.internal:2004/mcp`)
    - `excel` → `http://excel-mcp:8000/mcp` (or `http://host.docker.internal:2006/mcp`)
    - `word` → `http://word-mcp:8000/mcp` (or `http://host.docker.internal:2007/mcp`)
    - `pdf` → `http://pdf-mcp:8000/mcp` (or `http://host.docker.internal:2008/mcp`)
    - `analytics` → `http://analytics-mcp:8000/mcp` (or `http://host.docker.internal:2009/mcp`)
  - **Option 2 - Via MCPO (Recommended)**:
    - Single URL: `http://mcpo:8000/mcp` (or `http://host.docker.internal:2010/mcp`)
    - This exposes all 8 services through one endpoint
- Click "Test connection" for each; you should see the tool list returned.
- To use the OpenAPI proxy instead, add OpenAPI servers pointing at `http://localhost:2010/<tool>/openapi.json` (or `http://mcpo:8000/<tool>/openapi.json` on `mcp-net`), where `<tool>` is `time`, `filesystem`, `memory`, `email`, `excel`, `word`, `pdf`, or `analytics`.

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
- Health endpoints (all services):
  ```bash
  # Core services
  curl http://localhost:2001/healthz  # time
  curl http://localhost:2002/healthz  # filesystem
  curl http://localhost:2003/healthz  # memory
  curl http://localhost:2004/healthz  # email

  # Document generation services
  curl http://localhost:2006/healthz  # excel
  curl http://localhost:2007/healthz  # word
  curl http://localhost:2008/healthz  # pdf
  curl http://localhost:2009/healthz  # analytics
  ```
  Each should return: `ok`
- MCPO OpenAPI docs (verify all services):
  ```bash
  curl -I http://localhost:2010/time/docs
  curl -I http://localhost:2010/analytics/docs
  curl -I http://localhost:2010/excel/docs
  ```
  Each should return HTTP 200
- Filesystem container sees demo data:
  ```bash
  docker compose --env-file .env exec filesystem-mcp ls /docs
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

### Email via MCPO/OpenAPI (attachment gotchas)
- The `/email/send` route in MCPO expects attachments as objects with `path` (optionally `filename`). Example payload:
  ```json
  {
    "to": ["user@example.com"],
    "subject": "Border Patrol Monthly Report - March 2024",
    "body_html": "<p>See attached.</p>",
    "attachments": [
      {"path": "bp_crossings_central.xlsx"},
      {"path": "bp_crossings_east.xlsx"}
    ]
  }
  ```
- Paths must be under `/attachments` inside the container (mapped from `./docs` by default). Absolute paths are normalized only if they stay under that root; anything else fails fast with a 400.

## Debugging tips
- Check service logs: `docker compose --env-file .env logs <service> -f`
- Verify MailHog SMTP connectivity from the email container:
  ```bash
  docker compose --env-file .env exec email-mcp nc -z mailhog 1025
  ```
- Validate attach path: container should see files at `${ATTACH_ROOT}`; use `docker compose exec email-mcp ls /attachments`.
