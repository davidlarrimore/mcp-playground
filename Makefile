COMPOSE ?= docker compose
ENV_FILE ?= .env

.PHONY: up down logs rebuild nuke ps email-local email-local-stop

up:
	$(COMPOSE) --env-file $(ENV_FILE) up -d

down:
	$(COMPOSE) --env-file $(ENV_FILE) down

logs:
	$(COMPOSE) --env-file $(ENV_FILE) logs -f

ps:
	$(COMPOSE) --env-file $(ENV_FILE) ps

rebuild:
	$(COMPOSE) --env-file $(ENV_FILE) build --pull --no-cache

nuke:
	$(COMPOSE) --env-file $(ENV_FILE) down -v --remove-orphans

email-local:
	chmod +x scripts/run_email_mcp_local.sh
	./scripts/run_email_mcp_local.sh

email-local-stop:
	pkill -f "python -m email_mcp.server" || true
