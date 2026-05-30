#!/usr/bin/env bash
set -euo pipefail

echo "== Paths =="
pwd
test -d "/Users/rl_home/Documents/Codex/Hermes_Agent/overlays/codex-delegate" && echo "overlay: present"
test -d "/Users/rl_home/.hermes/hermes-agent" && echo "live Hermes repo: present"

echo
echo "== Hermes health =="
curl -sS http://127.0.0.1:8642/health || true
echo

echo
echo "== oMLX health =="
curl -sS http://127.0.0.1:8000/health || true
echo

echo
echo "== Hermes plugins =="
/Users/rl_home/.local/bin/hermes plugins list || true

echo
echo "== Codex version =="
codex --version || true

echo
echo "== Codex env names only =="
env | cut -d= -f1 | grep -E 'OPENAI|CODEX' | sort || true

echo
echo "== Codex config summary =="
if [[ -f "${HOME}/.codex/config.toml" ]]; then
  awk '/^\[/ {print; next} /^[[:space:]]*(model|approval_policy|sandbox_mode|network_access|command|args|enabled)/ { if ($0 ~ /(key|token|secret|password|auth)/) { split($0,a,"="); print a[1]"= <redacted>" } else print }' "${HOME}/.codex/config.toml"
else
  echo "missing ~/.codex/config.toml"
fi

echo
echo "== Codex auth summary =="
python3 -c 'import json, pathlib; p=pathlib.Path.home()/".codex"/"auth.json"; d=json.loads(p.read_text()) if p.exists() else {}; print({"exists": p.exists(), "top_level_keys": sorted(d.keys()), "has_token_fields": any("token" in k.lower() or "key" in k.lower() for k in d)})'
