#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE="${ROOT}/configs/codex-delegate.config.toml"
TARGET="${HOME}/.codex/codex-delegate.config.toml"
BACKUP_DIR="${HOME}/.codex/backups"
STAMP="$(date +%Y%m%d-%H%M%S)"

echo "This installs an optional Codex delegate profile template."
echo "Source: ${SOURCE}"
echo "Target: ${TARGET}"
echo "No API fallback is enabled by this profile."

test -f "${SOURCE}"
mkdir -p "${BACKUP_DIR}"
if [[ -f "${TARGET}" ]]; then
  cp "${TARGET}" "${BACKUP_DIR}/codex-delegate.config.toml.${STAMP}.bak"
  echo "Backed up existing profile to ${BACKUP_DIR}/codex-delegate.config.toml.${STAMP}.bak"
fi

cp "${SOURCE}" "${TARGET}"
echo "Installed ${TARGET}"
