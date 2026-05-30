#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

required=(
  "AGENTS.md"
  "README.md"
  "docs/codex_hermes_end_to_end_optimization_guide.md"
  "tools/codex_delegate.py"
  "configs/codex-delegate.config.toml"
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

echo "Installed obsidian-gbrain plugin source check:"
"/Users/rl_home/Documents/Codex/Hermes_Agent/scripts/sync_obsidian_gbrain_plugin.sh" --check

echo "Live Hermes repo status:"
git -C /Users/rl_home/.hermes/hermes-agent status --short --branch
