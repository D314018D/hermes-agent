#!/usr/bin/env python3
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "verification_report.md"


def run(cmd, env=None, optional=False):
    try:
        result = subprocess.run(
            cmd,
            cwd=ROOT,
            env=env or os.environ.copy(),
            text=True,
            capture_output=True,
            check=False,
        )
        return {
            "cmd": " ".join(cmd),
            "returncode": result.returncode,
            "stdout": result.stdout[-4000:],
            "stderr": result.stderr[-4000:],
            "ok": result.returncode == 0,
            "optional": optional,
        }
    except Exception as exc:
        return {
            "cmd": " ".join(cmd),
            "returncode": -1,
            "stdout": "",
            "stderr": str(exc),
            "ok": False,
            "optional": optional,
        }


def main():
    results = []
    env = os.environ.copy()
    env["OBSIDIAN_VAULT_PATH"] = "./obsidian-vault"
    env["MIN_STORE_SCORE"] = "3"
    env["SAVE_RAW_CONTENT"] = "false"
    env["GBRAIN_ENABLED"] = "false"

    expected_page = ROOT / "obsidian-vault/00_Inbox/Gbrain_Review/2026-04-25-woolworths-n70-robot-test-unit-follow-up.md"

    results.append({
        "cmd": "environment",
        "returncode": 0,
        "stdout": f"Python={sys.version}\nROOT={ROOT}\ngbrain={shutil.which('gbrain')}",
        "stderr": "",
        "ok": True,
        "optional": False,
    })

    results.append(run([
        sys.executable,
        "scripts/ingest.py",
        "connectors/voice/example_wechat_woolworths_n70.json",
    ], env=env))

    content_checks = []
    if expected_page.exists():
        txt = expected_page.read_text(encoding="utf-8")
        for needle in [
            "## Compiled Truth",
            "## AI Summary",
            "status: \"staged\"",
            "review_status: \"pending\"",
            "## Timeline",
            "2026-04-25",
            "Woolworths",
            "N70",
            "2026-04-25-wechat-woolworths-n70.m4a",
        ]:
            content_checks.append((needle, needle in txt))
        content_checks.append(("no raw content by default", "## Raw Content" not in txt))
    else:
        content_checks.append((str(expected_page), False))

    results.append({
        "cmd": "content checks",
        "returncode": 0 if all(ok for _, ok in content_checks) else 1,
        "stdout": "\n".join([f"{'PASS' if ok else 'FAIL'} {needle}" for needle, ok in content_checks]),
        "stderr": "",
        "ok": all(ok for _, ok in content_checks),
        "optional": False,
    })

    if shutil.which("pytest"):
        results.append(run([sys.executable, "-m", "pytest", "tests", "-q"], env=env))
    else:
        results.append({
            "cmd": "pytest",
            "returncode": 0,
            "stdout": "PYTEST_SKIPPED: pytest not installed",
            "stderr": "",
            "ok": True,
            "optional": True,
        })

    if shutil.which("gbrain"):
        for cmd in [
            ["gbrain", "--version"],
            ["gbrain", "doctor", "--json"],
            ["gbrain", "import", "./obsidian-vault", "--no-embed"],
            ["gbrain", "embed", "--stale"],
            ["gbrain", "search", "Woolworths N70", "--limit", "3"],
            ["gbrain", "query", "What is the status of Woolworths N70 Robot Test Unit?"],
            ["gbrain", "extract", "links", "--source", "db", "--dry-run"],
            ["gbrain", "stats"],
        ]:
            results.append(run(cmd, env=env, optional=True))
    else:
        results.append({
            "cmd": "gbrain optional verification",
            "returncode": 0,
            "stdout": "GBRAIN_SKIPPED: gbrain not found on PATH",
            "stderr": "",
            "ok": True,
            "optional": True,
        })

    lines = [
        "# Verification Report",
        "",
        f"Generated: {datetime.now().isoformat()}",
        "",
    ]

    hard_failures = []
    for result in results:
        status = "PASS" if result["ok"] else ("WARN" if result["optional"] else "FAIL")
        if not result["ok"] and not result["optional"]:
            hard_failures.append(result["cmd"])
        lines.extend([
            f"## {status}: `{result['cmd']}`",
            "",
            f"Return code: `{result['returncode']}`",
            "",
            "### STDOUT",
            "```",
            result["stdout"],
            "```",
            "",
            "### STDERR",
            "```",
            result["stderr"],
            "```",
            "",
        ])

    lines.append("## Final Result")
    if hard_failures:
        lines.append("FAIL")
        lines.append("")
        lines.append("Hard failures:")
        lines.extend(f"- {failure}" for failure in hard_failures)
    else:
        lines.append("PASS")

    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(REPORT)
    return 1 if hard_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
