#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from env import load_local_env
from agent.runtime import HermesAgentRuntime


load_local_env()


def main() -> int:
    parser = argparse.ArgumentParser(description="Dispatch Telegram, WeChat, or WebUI payloads through the local Hermes runtime")
    parser.add_argument("payload", nargs="?", default="-", help="Payload JSON file path or - for stdin")
    args = parser.parse_args()

    if args.payload == "-":
        payload_text = sys.stdin.read()
    else:
        payload_text = Path(args.payload).read_text(encoding="utf-8")

    payload = json.loads(payload_text)
    result = HermesAgentRuntime().dispatch_payload(payload)
    print(
        json.dumps(
            {
                "route": result.route,
                "model": result.model,
                "summary": result.summary,
                "reply": result.reply,
                "actions": [
                    {
                        "tool": item.tool,
                        "ok": item.ok,
                        "result": item.result,
                        "error": item.error,
                    }
                    for item in result.actions
                ],
                "queue_path": result.queue_path,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
