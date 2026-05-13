#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from env import load_local_env
from routing.model_router import route_model


load_local_env()


def main() -> int:
    parser = argparse.ArgumentParser(description="Qwen-first Hermes model/tool router")
    parser.add_argument("text", nargs="?", default="")
    parser.add_argument("--stdin", action="store_true", help="Read request text from stdin")
    parser.add_argument("--modality", default="text")
    parser.add_argument("--attachment", action="append", default=[])
    parser.add_argument("--tts", action="store_true")
    parser.add_argument("--has-voice-clone", action="store_true")
    parser.add_argument("--router", action="store_true")
    parser.add_argument("--llm", action="store_true", help="Ask local Qwen/OMLX to choose the route")
    parser.add_argument("--llm-timeout", type=float, default=8.0)
    parser.add_argument("--source", default="manual")
    parser.add_argument("--no-log", action="store_true")
    args = parser.parse_args()

    text = sys.stdin.read() if args.stdin else args.text
    result = route_model(
        text=text,
        modality=args.modality,
        attachments=args.attachment,
        wants_tts=args.tts,
        has_voice_clone=args.has_voice_clone,
        force_router=args.router,
        log_decision=not args.no_log,
        source=args.source,
        use_llm_router=args.llm,
        llm_timeout=args.llm_timeout,
    )
    print(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
