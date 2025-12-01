1. Final Part 2 architecture

All running on a shared Docker network:
	•	Open WebUI (Running externally, no need to setup)
	    •	Separate project/container (as you asked).
	    •	Uses LiteLLM as its LLM backend (Running externally, no need to setup)
	•	MCP servers needed (all HTTP / Streamable HTTP):
	1.	Time MCP – current time & timezone conversions.
	2.	Filesystem MCP – read/write files in a bounded demo directory.
	3.	Memory MCP – persistent “knowledge graph” memory (for the “gets smarter over time” arc).
	4.	Custom Email MCP – calls SMTP to send messages with real MIME attachments.
	5.	(Optional) KPI / Scenario MCP – small custom MCP that encapsulates your Week 8 workflow logic so the agent can call one higher-level tool like run_course_pipeline.
	•	MailHog – free SMTP test server + web UI to view emails and attachments.  ￼

All of these live on a Docker network, e.g. mcp-net, so each service can reach others via container name (e.g. mailhog:1025, filesystem-mcp:8000, etc.).

⸻

2. MCP servers you’ll install (with concrete links)

2.1 Reference servers (Docker Catalog / official MCP servers)

These come pre-packaged by Docker / Anthropic as “Reference MCP Servers” with Docker images:
	1.	Time MCP (Reference)
	•	Purpose: get current time, convert between timezones.  ￼
	•	Docker image: mcp/time
	•	Docs (Docker MCP Catalog – Time):

https://hub.docker.com/mcp/server/time/overview


	2.	Memory MCP (Reference)
	•	Purpose: knowledge-graph memory so the agent can remember users, course state, etc.  ￼
	•	Docker image: mcp/memory
	•	Docs (Docker MCP Catalog – Memory):

https://hub.docker.com/mcp/server/memory/overview


	3.	Filesystem MCP (Reference)
	•	Purpose: read/write/list/search files inside allowed directories; perfect for your “course docs on disk” part of the scenario.  ￼
	•	Docker image: mcp/filesystem
	•	Docs (Docker MCP Catalog – Filesystem):

https://hub.docker.com/mcp/server/filesystem/overview


	•	Backed by the official modelcontextprotocol/servers repo:  ￼

https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem



2.2 Custom Email MCP server (for MailHog + attachments)

There isn’t yet an official “email with attachments” reference MCP server, and generic SMTP MCP servers like smtp-edc don’t expose attachments as first-class parameters.  ￼

So for clean control and easy attachment support, I recommend a tiny custom MCP server:
	•	Name (your choice): email-smtp-mcp
	•	Tech stack: Python + official MCP Python SDK (mcp on PyPI).  ￼
	•	Template to start from: a Python MCP server template, e.g.:  ￼

https://github.com/BaranDev/mcp-server-template


	•	Transport: streamable_http on port 8000.
	•	Tools to expose (examples):
	•	send_email_with_attachments
	•	Args: to, cc, subject, body_html, body_text, attachments
	•	attachments = list of { "path": "relative/path/in/shared/volume", "filename": "Something.pdf" }
	•	preview_email (optional, returns JSON of how the email will look without sending).

This server will:
	1.	Build a MIME message using Python’s email.message.EmailMessage.
	2.	For each attachment:
	•	Join ATTACH_ROOT + path
	•	Read file bytes
	•	Add as MIME attachment with correct content-type.
	3.	Open an SMTP connection to MailHog at mailhog:1025 and send.

Because MailHog supports multipart MIME and viewing/downloading MIME parts, attachments will show up nicely in the MailHog UI.  ￼

2.3 (Optional) KPI / Scenario MCP server

If you want one “big button” for the second half of the demo (e.g., “Generate and send course reminder emails for all participants”), you can wrap your domain logic in a small custom MCP server, again using the Python SDK or the same template, with tools like:
	•	plan_lunch_and_learn_run
	•	build_course_summary
	•	send_all_course_emails

This server would internally call:
	•	Filesystem MCP → load scenario docs.
	•	Memory MCP → recall past runs.
	•	Email MCP → send final emails.

For links/templates, you can reuse the same Python MCP template as above.

⸻

3. Docker Compose layout (conceptual)

Below is a conceptual docker-compose.yml to show how the pieces hang together. You’ll keep Open WebUI + LiteLLM in their own project, but ensure they join the same Docker network (e.g. mcp-net).

version: "3.9"

networks:
  mcp-net:
    driver: bridge

volumes:
  memory-data: {}

services:
  # ---------- Email testing ----------
  mailhog:
    image: mailhog/mailhog:latest
    container_name: mailhog
    networks:
      - mcp-net
    ports:
      - "8025:8025"   # Web UI
      - "1025:1025"   # SMTP

  # ---------- Reference MCP servers ----------
  time-mcp:
    image: mcp/time:latest
    container_name: time-mcp
    networks:
      - mcp-net
    ports:
      - "8001:8000"   # Expose HTTP MCP
    # If needed, check the Docker MCP Catalog 'Manual installation'
    # for any extra env/flags – by default these images are built to
    # be usable as HTTP-based MCP servers.  [oai_citation:9‡Docker Hub](https://hub.docker.com/mcp/server/time/overview)

  filesystem-mcp:
    image: mcp/filesystem:latest
    container_name: filesystem-mcp
    networks:
      - mcp-net
    ports:
      - "8002:8000"
    volumes:
      - ./demo-data:/demo-data:rw   # Course docs for the scenario

  memory-mcp:
    image: mcp/memory:latest
    container_name: memory-mcp
    networks:
      - mcp-net
    ports:
      - "8003:8000"
    volumes:
      - memory-data:/data  # Persistent knowledge graph store

  # ---------- Custom Email MCP (HTTP) ----------
  email-mcp:
    build: ./email-mcp     # Your Dockerfile wraps the Python MCP server
    container_name: email-mcp
    networks:
      - mcp-net
    ports:
      - "8004:8000"
    environment:
      SMTP_HOST: mailhog
      SMTP_PORT: "1025"
      SMTP_FROM_DEFAULT: "noreply@example.test"
      ATTACH_ROOT: /attachments
    volumes:
      - ./demo-data:/attachments:ro

For each official MCP image (mcp/time, mcp/memory, mcp/filesystem), confirm any HTTP-specific flags in the Docker MCP Catalog’s Manual installation before the workshop, but the pattern will remain “image + port 8000 + your volume(s)”.  ￼

Your Open WebUI + LiteLLM project then:
	•	Joins mcp-net
	•	Talks to LiteLLM as its LLM provider
	•	Hits MCP servers by Docker hostnames: http://time-mcp:8000, etc.

⸻

4. Connecting MCP HTTP servers to Open WebUI

Open WebUI already supports MCP (Streamable HTTP) as an external tool type.  ￼

For each MCP server:
	1.	Open WebUI → Settings → Tools (or External Tools).
	2.	Click “Add Tool Server”.
	3.	Set:
	•	Type: MCP (Streamable HTTP)
	•	Name: e.g. time, filesystem, memory, email
	•	Server URL: based on your Docker network, for example:
	•	Time: http://time-mcp:8000
	•	Filesystem: http://filesystem-mcp:8000
	•	Memory: http://memory-mcp:8000
	•	Email: http://email-mcp:8000
	4.	If your HTTP servers expect an API key, provide it (for the demo, you can leave auth off and keep everything on localhost / dev network).
	5.	Hit Test connection and confirm the tools list shows up.

Now, inside a chat:
	•	Use the model routed through LiteLLM.
	•	When the agent needs to call a tool, it will hit the MCP endpoints directly.

⸻

5. Email integration with MailHog + attachments

5.1 MailHog setup (cheap + free)
	•	Use the official Docker image: mailhog/mailhog.  ￼
	•	SMTP on 1025 and Web UI on 8025 by default.
	•	In Docker Compose above, we exposed both ports so you can show the MailHog UI live.

MailHog features relevant to your demo:
	•	Captures all outgoing SMTP mail (no real delivery).
	•	Supports multipart MIME, including attached files; you can view and download them in the web UI.  ￼

5.2 How your Email MCP server works

Inside email-mcp (Python sketch, not full code):
	•	Uses MCP Python SDK for HTTP transport.  ￼
	•	Defines a tool:

@server.tool()
async def send_email_with_attachments(
    to: list[str],
    subject: str,
    body_html: str | None = None,
    body_text: str | None = None,
    attachments: list[dict] | None = None,
) -> dict:
    ...


	•	For each attachment:
	•	Build an absolute path: ATTACH_ROOT + attachment["path"].
	•	Read file bytes.
	•	Attach as MIME part.
	•	Use smtplib.SMTP(host=SMTP_HOST, port=SMTP_PORT) to send to mailhog.

Demo flow to highlight:
	1.	Agent uses Filesystem MCP to locate a scenario file (e.g., demo-data/CourseOutlineWeek8.pdf).
	2.	Agent calls Email MCP with:
	•	attachments=[{"path": "CourseOutlineWeek8.pdf", "filename": "Week8Outline.pdf"}]
	3.	MailHog captures the message; you refresh the MailHog UI at http://localhost:8025 and click the message to show:
	•	Recipient
	•	Subject
	•	Body
	•	Downloadable PDF attachment.

That visually sells “agentic” behavior and attachment handling without any paid services.

⸻

6. “Increasingly more connected & smarter” demo ladder

Here’s how you can structure Part 2 as a progressive story:
	1.	Level 0 – Plain LLM in Open WebUI
	•	Prompt: “Draft a generic lunch-and-learn invite.”
	•	No tools. Just ChatGPT-style behavior.
	2.	Level 1 – Add Time MCP
	•	Show the model calling time to pick correct dates/time zones for your audience.  ￼
	•	Prompt: “Schedule this invite for the next available Thursday at 12pm Eastern, and include the date in the email.”
	3.	Level 2 – Add Filesystem MCP
	•	Mount your scenario docs under ./demo-data.
	•	Have the agent call filesystem tools to:
	•	List available course docs.
	•	Read a specific lesson outline.
	•	Prompt: “Look at the Lunch and Learn Week 8 outline in the shared folder and personalize the invite based on the topics covered.”
	4.	Level 3 – Add Memory MCP
	•	Use memory MCP to store participant data and preferences between runs (e.g., who attended Week 7, what interests they have).  ￼
	•	Show that on a second run, the agent:
	•	Recalls who attended before.
	•	Tailors messaging (“Since you attended Week 7, we’ll be building directly on the MCP knowledge you saw last time …”).
	5.	Level 4 – Email MCP + MailHog
	•	Now give the agent permission to call send_email_with_attachments.
	•	Prompt:
“For everyone in our participants.json file, generate a personalized invite based on their attendance history, attach the Week 8 outline PDF, and send the emails. Then summarize who got what.”
	•	Flip to the MailHog UI and show the queue of messages with attachments.
	6.	(Optional) Level 5 – KPI / Scenario MCP
	•	Wrap the whole workflow into a single MCP tool:
	•	run_lunch_and_learn_campaign
	•	Show that the model can call one higher-level tool that orchestrates filesystem + memory + email under the hood.
