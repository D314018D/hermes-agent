#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODE="--dry-run"
LIMIT="20"
VERBOSE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      MODE="--dry-run"
      shift
      ;;
    --write)
      MODE="--write"
      shift
      ;;
    --limit)
      LIMIT="${2:-20}"
      shift 2
      ;;
    --verbose)
      VERBOSE="--verbose"
      shift
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

python3 "$SCRIPT_DIR/process_review.py" "$MODE" --limit "$LIMIT" $VERBOSE
python3 "$SCRIPT_DIR/route_staging.py" "$MODE" --limit "$LIMIT" $VERBOSE
python3 "$SCRIPT_DIR/run_gbrain_extract.py" "$MODE" --limit "$LIMIT" $VERBOSE
python3 "$SCRIPT_DIR/update_mocs.py" "$MODE" --limit "$LIMIT" $VERBOSE
python3 "$SCRIPT_DIR/check_backlinks.py" "$MODE" --limit "$LIMIT" $VERBOSE
