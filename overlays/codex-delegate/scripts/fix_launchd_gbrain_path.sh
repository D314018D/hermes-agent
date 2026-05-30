#!/usr/bin/env bash
set -euo pipefail

PLIST="/Users/rl_home/Library/LaunchAgents/ai.hermes.gateway.plist"
OLD="/Users/rl_home/Documents/Codex/Hermes Agent/integrations/gbrain-obsidian"
NEW="/Users/rl_home/Documents/Codex/Hermes_Agent/integrations/gbrain-obsidian"
BACKUP_DIR="/Users/rl_home/.hermes/backups"
STAMP="$(date +%Y%m%d-%H%M%S)"

echo "This script corrects only HERMES_OBSIDIAN_GBRAIN_ROOT in the Hermes launchd plist."
echo "It does not edit Hermes core or plugin source."
echo "Old: ${OLD}"
echo "New: ${NEW}"

test -f "${PLIST}"
test -d "${NEW}"
mkdir -p "${BACKUP_DIR}"
cp "${PLIST}" "${BACKUP_DIR}/ai.hermes.gateway.plist.${STAMP}.bak"

python3 -c 'from pathlib import Path; import sys; plist=Path(sys.argv[1]); old=sys.argv[2]; new=sys.argv[3]; text=plist.read_text(); changed=text.replace(old, new); assert text != changed, "old path not found"; plist.write_text(changed)' "${PLIST}" "${OLD}" "${NEW}"

echo "Updated plist. Backup: ${BACKUP_DIR}/ai.hermes.gateway.plist.${STAMP}.bak"
echo "Reload/restart Hermes gateway separately after approval, then verify http://127.0.0.1:8642/health."
