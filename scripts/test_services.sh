#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ENV_FILE:-${ROOT_DIR}/.env}"

if [[ -f "${ENV_FILE}" ]]; then
  # shellcheck disable=SC1090
  source "${ENV_FILE}"
fi

TIME_PORT="${TIME_MCP_PORT:-2001}"
FILES_PORT="${FILESYSTEM_MCP_PORT:-2002}"
MEM_PORT="${MEMORY_MCP_PORT:-2003}"
EMAIL_PORT="${EMAIL_MCP_PORT:-2004}"
MAILHOG_PORT="${MAILHOG_WEB_PORT:-2005}"
TEST_TO="${EMAIL_TEST_TO:-ops@example.com}"

HOST="${HOST_OVERRIDE:-localhost}"

fail() { echo "❌ $*" >&2; exit 1; }
ok() { echo "✅ $*"; }

curl_check() {
  local name=$1 url=$2
  if curl -fsS "$url" >/dev/null; then
    ok "$name healthy at $url"
  else
    fail "$name failed at $url"
  fi
}

echo "== Health checks =="
curl_check "time" "http://${HOST}:${TIME_PORT}/healthz"
curl_check "filesystem" "http://${HOST}:${FILES_PORT}/healthz"
curl_check "memory" "http://${HOST}:${MEM_PORT}/healthz"
curl_check "email" "http://${HOST}:${EMAIL_PORT}/healthz"

echo "== Filesystem list =="
docker compose --env-file "${ENV_FILE}" exec -T filesystem-mcp ls /demo-data || fail "filesystem container cannot list /demo-data"
ok "filesystem container can see /demo-data"

echo "== Memory storage =="
docker compose --env-file "${ENV_FILE}" exec -T memory-mcp ls /data || fail "memory container cannot access /data"
ok "memory container can access /data"

echo "== Email send (check MailHog UI) =="
SEND_BODY=$(printf '{"to":["%s"],"subject":"Health check","body_text":"MCP stack is alive"}' "${TEST_TO}")
if curl -fsS -X POST "http://${HOST}:${EMAIL_PORT}/send" -H "Content-Type: application/json" -d "${SEND_BODY}" >/dev/null; then
  ok "email send endpoint responded"
  echo "Open MailHog UI at http://${HOST}:${MAILHOG_PORT} to confirm message."
else
  fail "email send failed"
fi

echo "All checks completed."
