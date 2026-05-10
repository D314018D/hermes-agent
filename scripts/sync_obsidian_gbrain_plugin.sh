#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source_dir="${repo_root}/integrations/gbrain-obsidian/.hermes/plugins/obsidian-gbrain"
target_dir="${HERMES_OBSIDIAN_GBRAIN_PLUGIN_DIR:-${HOME}/.hermes/plugins/obsidian-gbrain}"

usage() {
  cat <<'USAGE'
Usage:
  scripts/sync_obsidian_gbrain_plugin.sh --check
  scripts/sync_obsidian_gbrain_plugin.sh --apply

Checks or syncs the repository's obsidian-gbrain plugin source into the active
Hermes user plugin directory. The script only compares/copies source files and
excludes Python cache files.
USAGE
}

mode="${1:---check}"
case "${mode}" in
  --check|--apply)
    ;;
  -h|--help)
    usage
    exit 0
    ;;
  *)
    usage >&2
    exit 2
    ;;
esac

if [[ ! -d "${source_dir}" ]]; then
  echo "Source plugin directory not found: ${source_dir}" >&2
  exit 1
fi

if [[ "${mode}" == "--check" ]]; then
  if [[ ! -d "${target_dir}" ]]; then
    echo "Target plugin directory not found: ${target_dir}" >&2
    exit 1
  fi
  diff -ru \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    "${source_dir}" \
    "${target_dir}"
  echo "obsidian-gbrain plugin source matches installed plugin."
  exit 0
fi

mkdir -p "${target_dir}"
rsync -a --delete \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  "${source_dir}/" \
  "${target_dir}/"
echo "Synced obsidian-gbrain plugin to ${target_dir}"
