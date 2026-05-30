#!/usr/bin/env bash
set -euo pipefail

ROOT="/Users/rl_home/Documents/Codex/Hermes_Agent/overlays/codex-delegate"
PROFILE="${HOME}/.codex/codex-delegate.config.toml"
PLUGIN="${HOME}/.hermes/plugins/codex-delegate"

echo "Rollback helper for optional codex-delegate runtime artifacts."
echo "It does not delete the source overlay automatically."

if [[ -L "${PLUGIN}" ]]; then
  rm "${PLUGIN}"
  echo "Removed plugin symlink: ${PLUGIN}"
elif [[ -d "${PLUGIN}" ]]; then
  echo "Plugin directory exists and was not removed automatically: ${PLUGIN}"
fi

if [[ -f "${PROFILE}" ]]; then
  rm "${PROFILE}"
  echo "Removed optional Codex profile: ${PROFILE}"
fi

echo "Source overlay remains at ${ROOT}."
curl -sS http://127.0.0.1:8642/health || true
echo
