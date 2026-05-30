#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROFILE="${1:-codex-delegate}"
BACKUP_DIR="${HOME}/.codex/backups"
STAMP="$(date +%Y%m%d-%H%M%S)"

case "${PROFILE}" in
  codex-delegate)
    SOURCE="${ROOT}/configs/codex-delegate.config.toml"
    TARGET="${HOME}/.codex/codex-delegate.config.toml"
    ;;
  local_private_coder)
    SOURCE="${ROOT}/configs/local_private_coder.config.toml"
    TARGET="${HOME}/.codex/local_private_coder.config.toml"
    ;;
  *)
    echo "Usage: $0 [codex-delegate|local_private_coder]" >&2
    exit 2
    ;;
esac

echo "This installs an optional Codex profile template."
echo "Source: ${SOURCE}"
echo "Target: ${TARGET}"
echo "No API fallback is enabled by this installer."

test -f "${SOURCE}"
mkdir -p "${BACKUP_DIR}"
if [[ -f "${TARGET}" ]]; then
  backup_name="$(basename "${TARGET}").${STAMP}.bak"
  cp "${TARGET}" "${BACKUP_DIR}/${backup_name}"
  echo "Backed up existing profile to ${BACKUP_DIR}/${backup_name}"
fi

cp "${SOURCE}" "${TARGET}"
echo "Installed ${TARGET}"

if [[ "${PROFILE}" == "local_private_coder" ]]; then
  echo "This profile expects OMLX_API_KEY in the environment at runtime."
  echo "It does not change ~/.codex/config.toml or the global Codex default model."
fi
