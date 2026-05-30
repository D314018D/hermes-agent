#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLUGIN="${HOME}/.hermes/plugins/codex-delegate"
BACKUP_DIR="${HOME}/.hermes/backups"
STAMP="$(date +%Y%m%d-%H%M%S)"

echo "Installing codex-delegate as a Hermes user plugin."
echo "Source: ${ROOT}"
echo "Target: ${PLUGIN}"
echo "This script does not modify Hermes core and does not restart the gateway."

test -f "${ROOT}/plugin.yaml"
test -f "${ROOT}/tools/codex_delegate.py"
curl -sS http://127.0.0.1:8642/health >/dev/null || {
  echo "Hermes gateway health check failed; install aborted." >&2
  exit 1
}

mkdir -p "$(dirname "${PLUGIN}")" "${BACKUP_DIR}"

if [[ -L "${PLUGIN}" ]]; then
  current_target="$(readlink "${PLUGIN}")"
  if [[ "${current_target}" == "${ROOT}" ]]; then
    echo "Plugin symlink already points to source overlay."
  else
    mv "${PLUGIN}" "${BACKUP_DIR}/codex-delegate.symlink.${STAMP}"
    ln -s "${ROOT}" "${PLUGIN}"
    echo "Backed up prior symlink and installed overlay symlink."
  fi
elif [[ -e "${PLUGIN}" ]]; then
  mv "${PLUGIN}" "${BACKUP_DIR}/codex-delegate.${STAMP}.bak"
  ln -s "${ROOT}" "${PLUGIN}"
  echo "Backed up prior plugin path and installed overlay symlink."
else
  ln -s "${ROOT}" "${PLUGIN}"
  echo "Installed overlay symlink."
fi

echo "Rollback: remove ${PLUGIN}, or restore backup from ${BACKUP_DIR}."
