#!/usr/bin/env python3
from __future__ import annotations

from common import options_from_args, parse_common, preflight, run_gbrain


def main() -> int:
    parser = parse_common("Run low-resource GBrain extraction tasks under the Hermes GBrain lock.")
    args = parser.parse_args()
    opts = options_from_args(args)
    preflight(opts)

    dry_run = not opts.write
    for task in (["extract", "links", "--source", "db"], ["extract", "timeline", "--source", "db"]):
        code = run_gbrain(list(task), dry_run=dry_run, timeout_seconds=300)
        if code != 0:
            return code
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
