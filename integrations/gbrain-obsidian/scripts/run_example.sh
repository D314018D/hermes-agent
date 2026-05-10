#!/usr/bin/env bash
set -euo pipefail

export OBSIDIAN_VAULT_PATH="./obsidian-vault"
export MIN_STORE_SCORE=3
export SAVE_RAW_CONTENT=false

python scripts/ingest.py connectors/text/example_input.json
