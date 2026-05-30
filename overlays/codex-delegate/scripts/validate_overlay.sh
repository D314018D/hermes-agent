#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

required=(
  "AGENTS.md"
  "README.md"
  "docs/codex_hermes_end_to_end_optimization_guide.md"
  "docs/local_omlx_codex_profile.md"
  "tools/codex_delegate.py"
  "configs/codex-delegate.config.toml"
  "configs/local_private_coder.config.toml"
  "policies/routing_policy.yaml"
  "policies/privacy_policy.yaml"
  "policies/memory_policy.yaml"
  "prompts/codex_context_pack.md"
  "prompts/codex_task_summary_schema.md"
  "prompts/codex_memory_candidate_schema.md"
  "prompts/codex_skill_candidate_schema.md"
  "scripts/inspect_environment.sh"
  "scripts/install_overlay.sh"
  "scripts/validate_overlay.sh"
  "scripts/install_profile.sh"
  "scripts/fix_launchd_gbrain_path.sh"
  "scripts/rollback_overlay.sh"
  "tests/test_codex_delegate.py"
)

for item in "${required[@]}"; do
  test -e "${ROOT}/${item}" || {
    echo "Missing required file: ${item}" >&2
    exit 1
  }
done

python3 -m py_compile "${ROOT}/tools/codex_delegate.py"
PYTHONPATH="${ROOT}" python3 -m unittest discover -s "${ROOT}/tests" -p 'test_*.py'

for log_name in router_decision codex_delegate api_approval memory_candidate tool_calls; do
  test -d "${ROOT}/logs" || {
    echo "Missing logs directory" >&2
    exit 1
  }
  case "${log_name}" in
    router_decision|codex_delegate|api_approval|memory_candidate|tool_calls) ;;
    *) exit 1 ;;
  esac
done

check_http() {
  local label="$1"
  local url="$2"
  local output
  echo "${label}:"
  if output="$(curl -sS "${url}" 2>&1)"; then
    echo "${output}"
  else
    echo "unavailable from this script context: ${output}"
  fi
}

check_http "Hermes health" "http://127.0.0.1:8642/health"
echo

check_http "oMLX health" "http://127.0.0.1:8000/health"
echo

echo "oMLX authenticated models:"
python3 - <<'PY'
import json
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

settings = Path.home() / ".omlx" / "settings.json"
if not settings.exists():
    print("missing ~/.omlx/settings.json auth.api_key; set OMLX_API_KEY manually for runtime validation")
    raise SystemExit(0)
data = json.loads(settings.read_text(encoding="utf-8"))
api_key = (data.get("auth") or {}).get("api_key") or ""
if not api_key:
    print("missing ~/.omlx/settings.json auth.api_key; set OMLX_API_KEY manually for runtime validation")
    raise SystemExit(0)

request = Request(
    "http://127.0.0.1:8000/v1/models",
    headers={"Authorization": f"Bearer {api_key}"},
)
try:
    with urlopen(request, timeout=10) as response:
        models = json.loads(response.read().decode("utf-8"))
except URLError as exc:
    print(f"unavailable from this script context: {exc}")
else:
    print([item.get("id") for item in models.get("data", [])])
PY
echo

echo "Codex local_private_coder profile template:"
grep -q 'model_provider = "localmlx"' "${ROOT}/configs/local_private_coder.config.toml"
grep -q 'model = "Qwen3.5-9B-OptiQ-4bit"' "${ROOT}/configs/local_private_coder.config.toml"
grep -q 'wire_api = "responses"' "${ROOT}/configs/local_private_coder.config.toml"
grep -q 'env_key = "OMLX_API_KEY"' "${ROOT}/configs/local_private_coder.config.toml"
echo "template ok"
echo

echo "Codex global default guard:"
if [[ -f "${HOME}/.codex/config.toml" ]] && grep -q '^model_provider = "localmlx"' "${HOME}/.codex/config.toml"; then
  echo "Global Codex config currently defaults to localmlx; expected non-local global default." >&2
  exit 1
fi
echo "global default has not been switched to localmlx"
echo

echo "Installed local_private_coder profile validation:"
if [[ -f "${HOME}/.codex/local_private_coder.config.toml" ]]; then
  if [[ -n "${OMLX_API_KEY:-}" ]]; then
    codex --strict-config --profile local_private_coder exec \
      "Reply with OK only. Do not inspect, create, modify, or delete files."
  else
    echo "installed profile present; set OMLX_API_KEY before running live Codex profile validation"
  fi
else
  echo "not installed; run ./scripts/install_profile.sh local_private_coder after approval"
fi
echo

echo "Installed obsidian-gbrain plugin source check:"
"/Users/rl_home/Documents/Codex/Hermes_Agent/scripts/sync_obsidian_gbrain_plugin.sh" --check

echo "Live Hermes repo status:"
git -C /Users/rl_home/.hermes/hermes-agent status --short --branch
