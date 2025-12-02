#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ENV_FILE:-${ROOT_DIR}/.env}"
VENV_DIR="${ROOT_DIR}/.venv"
PYTHON_BIN="${PYTHON_BIN:-python3}"

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  echo "Python interpreter '${PYTHON_BIN}' not found. Set PYTHON_BIN to a Python >=3.10 executable." >&2
  exit 1
fi

PY_VERSION="$(${PYTHON_BIN} - <<'PY'
import sys
print(f\"{sys.version_info.major}.{sys.version_info.minor}\")
PY
)"
PY_MAJOR="${PY_VERSION%%.*}"
PY_MINOR="${PY_VERSION#*.}"

if [ "${PY_MAJOR}" -lt 3 ] || { [ "${PY_MAJOR}" -eq 3 ] && [ "${PY_MINOR}" -lt 10 ]; }; then
  echo "FastMCP 2.x requires Python >=3.10 (found ${PY_VERSION}). Please point PYTHON_BIN to a newer interpreter." >&2
  exit 1
fi

if [[ -f "${ENV_FILE}" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "${ENV_FILE}"
  set +a
fi

export ATTACH_ROOT="${ATTACH_ROOT:-${ROOT_DIR}/docs}"
export SMTP_HOST="${SMTP_HOST:-localhost}"
export SMTP_PORT="${SMTP_PORT:-1025}"
export SMTP_FROM_DEFAULT="${SMTP_FROM_DEFAULT:-noreply@example.test}"
export LOG_LEVEL="${LOG_LEVEL:-INFO}"

"${PYTHON_BIN}" -m venv "${VENV_DIR}"
source "${VENV_DIR}/bin/activate"
python -m pip install --upgrade pip
python -m pip install -r "${ROOT_DIR}/email-mcp/requirements.txt"

cd "${ROOT_DIR}/email-mcp"
exec python -m email_mcp.server
