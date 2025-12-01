#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ENV_FILE:-${ROOT_DIR}/.env}"
VENV_DIR="${ROOT_DIR}/.venv"

if [[ -f "${ENV_FILE}" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "${ENV_FILE}"
  set +a
fi

export ATTACH_ROOT="${ATTACH_ROOT:-${ROOT_DIR}/demo-data}"
export SMTP_HOST="${SMTP_HOST:-localhost}"
export SMTP_PORT="${SMTP_PORT:-1025}"
export SMTP_FROM_DEFAULT="${SMTP_FROM_DEFAULT:-noreply@example.test}"
export LOG_LEVEL="${LOG_LEVEL:-INFO}"

python3 -m venv "${VENV_DIR}"
source "${VENV_DIR}/bin/activate"
python -m pip install --upgrade pip
python -m pip install -r "${ROOT_DIR}/email-mcp/requirements.txt"

cd "${ROOT_DIR}/email-mcp"
exec python -m email_mcp.server
