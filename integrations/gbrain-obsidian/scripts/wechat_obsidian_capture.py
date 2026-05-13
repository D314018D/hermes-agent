#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HERMES_CONFIG = Path.home() / ".hermes" / "config.yaml"
LOG_PATH = ROOT / "wechat_obsidian_capture.log"

sys.path.insert(0, str(ROOT))

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--message", required=False, default="")
    parser.add_argument("--platform", default="wechat")
    parser.add_argument("--session-id", default="")
    parser.add_argument("--chat-id", default="")
    args = parser.parse_args()

    record = {
        "ok": False,
        "deprecated": True,
        "message": (args.message or "").strip(),
        "replacement": "python3 scripts/hermes_dispatch.py -",
        "reason": "wechat_obsidian_capture.py only captured fragments into Obsidian and did not provide a real Hermes execution chain.",
    }
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(json.dumps(record, ensure_ascii=False, indent=2))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
