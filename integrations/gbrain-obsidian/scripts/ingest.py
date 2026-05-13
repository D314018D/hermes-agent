#!/usr/bin/env python3
import json
import os
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from env import load_local_env
from ingestion.schema import IngestInput
from ingestion.pipeline import ingest


load_local_env()

def main():
    parser = argparse.ArgumentParser(description="Run local Hermes/Gbrain/Obsidian ingestion")
    parser.add_argument("input", nargs="?", default="-", help="Input JSON path or - for stdin")
    parser.add_argument("--dry-run", action="store_true", help="Process and resolve without writing Markdown or memory logs")
    args = parser.parse_args()

    if args.input == "-" and sys.stdin.isatty():
        print("Usage: python scripts/ingest.py input.json")
        print("   or: cat input.json | python scripts/ingest.py -")
        print("   add --dry-run to preview without writing files")
        sys.exit(1)

    if args.dry_run:
        os.environ["GBRAIN_DRY_RUN"] = "true"

    if args.input != "-":
        payload_text = Path(args.input).read_text(encoding="utf-8")
    else:
        payload_text = sys.stdin.read()

    payload = json.loads(payload_text)
    item = IngestInput.from_payload(payload)
    result = ingest(item)

    print(json.dumps({
        "should_store": result.should_store,
        "score": result.score,
        "note_type": result.note_type,
        "classification_confidence": result.classification_confidence,
        "classification_reason": result.classification_reason,
        "status": result.status,
        "review_status": result.review_status,
        "sensitivity": result.sensitivity,
        "confidence": result.confidence,
        "suggested_folder": result.suggested_folder,
        "final_folder": result.final_folder,
        "output_path": result.output_path,
        "processing_log_path": result.processing_log_path,
        "duplicate_of": result.duplicate_of,
        "dry_run": result.dry_run,
        "action_items": result.action_items,
        "entities": result.entities,
        "tags": result.tags,
    }, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
