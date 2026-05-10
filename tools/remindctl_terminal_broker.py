#!/usr/bin/env python3
"""Run remindctl through Terminal.app when LaunchAgent TCC blocks direct access."""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path


REMINDCTL = "/opt/homebrew/bin/remindctl"
EXIT_MARKER = "__HERMES_REMINDCTL_EXIT__:"


def _terminal_script(args: list[str], output_path: Path) -> str:
    quoted_args = " ".join(shlex.quote(arg) for arg in args)
    quoted_output = shlex.quote(str(output_path))
    return (
        f"{{ {shlex.quote(REMINDCTL)} {quoted_args}; "
        f"ec=$?; printf '\\n{EXIT_MARKER}%s\\n' \"$ec\"; }} "
        f"> {quoted_output} 2>&1; exit"
    )


def _command_file(script: str) -> Path:
    path = Path(tempfile.gettempdir()) / f"hermes-remindctl-{uuid.uuid4().hex}.command"
    path.write_text(f"#!/bin/zsh\n{script}\n", encoding="utf-8")
    path.chmod(0o755)
    return path


def _parse_result(text: str) -> tuple[str, int | None]:
    exit_code: int | None = None
    lines: list[str] = []
    for line in text.splitlines():
        if line.startswith(EXIT_MARKER):
            try:
                exit_code = int(line.removeprefix(EXIT_MARKER).strip())
            except ValueError:
                exit_code = 1
            continue
        lines.append(line)
    return "\n".join(lines).strip(), exit_code


def main(argv: list[str]) -> int:
    if not argv:
        print("Usage: remindctl_terminal_broker.py <remindctl args...>", file=sys.stderr)
        return 2

    output_path = Path(tempfile.gettempdir()) / f"hermes-remindctl-{uuid.uuid4().hex}.txt"
    script = _terminal_script(argv, output_path)
    command_path = _command_file(script)

    proc = subprocess.run(
        ["open", "-a", "Terminal", str(command_path)],
        text=True,
        capture_output=True,
        timeout=15,
    )
    if proc.returncode != 0:
        if proc.stdout.strip():
            print(proc.stdout.strip())
        if proc.stderr.strip():
            print(proc.stderr.strip(), file=sys.stderr)
        return proc.returncode

    deadline = time.time() + float(os.environ.get("HERMES_REMINDCTL_BROKER_TIMEOUT", "30"))
    while time.time() < deadline:
        if output_path.exists():
            text = output_path.read_text(encoding="utf-8", errors="replace")
            output, exit_code = _parse_result(text)
            if exit_code is not None:
                if output:
                    print(output)
                try:
                    output_path.unlink()
                except OSError:
                    pass
                try:
                    command_path.unlink()
                except OSError:
                    pass
                return exit_code
        time.sleep(0.25)

    try:
        command_path.unlink()
    except OSError:
        pass
    print(f"Timed out waiting for Terminal.app remindctl result: {output_path}", file=sys.stderr)
    return 124


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
