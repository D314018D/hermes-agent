#!/bin/zsh

set -euo pipefail

KEYCHAIN_SERVICE="${KEYCHAIN_SERVICE:-openai_api_key}"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
ENV_FILE="$HERMES_HOME/.env"
TARGET_VAR="${TARGET_VAR:-HERMES_OPENAI_API_KEY}"

mkdir -p "$HERMES_HOME"
touch "$ENV_FILE"

api_key="$(security find-generic-password -a "$USER" -s "$KEYCHAIN_SERVICE" -w 2>/dev/null || true)"

if [[ -z "$api_key" ]]; then
  echo "No macOS Keychain item found for service '$KEYCHAIN_SERVICE'."
  echo "Save it first with:"
  echo "security add-generic-password -a \"\$USER\" -s \"$KEYCHAIN_SERVICE\" -w 'your_api_key_here'"
  exit 1
fi

tmp_file="$(mktemp)"
trap 'rm -f "$tmp_file"' EXIT

if [[ -f "$ENV_FILE" ]]; then
  grep -v "^${TARGET_VAR}=" "$ENV_FILE" > "$tmp_file" || true
fi
printf "%s=%s\n" "$TARGET_VAR" "$api_key" >> "$tmp_file"
mv "$tmp_file" "$ENV_FILE"

echo "Synced macOS Keychain service '$KEYCHAIN_SERVICE' to $ENV_FILE as $TARGET_VAR."
