#!/usr/bin/env python3
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from maintenance.gbrain_cli import run_gbrain_command


def main() -> int:
    query = " ".join(sys.argv[1:]) or "What changed recently?"
    result = run_gbrain_command(["query", query], command_timeout_seconds=120)
    if result.get("skipped"):
        print(f"GBRAIN_SKIPPED: {result.get('reason', 'gbrain unavailable')}")
        return 0
    print(result.get("stdout", ""))
    if result.get("stderr"):
        print(result["stderr"], file=sys.stderr)
    return int(result.get("returncode", 1))


if __name__ == "__main__":
    raise SystemExit(main())
