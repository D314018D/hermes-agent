import subprocess

from .gbrain_cli import gbrain_command, gbrain_env, gbrain_lock


def run_maintenance() -> list[dict]:
    command_args = [
        ["embed", "--stale"],
        ["extract", "links", "--source", "db"],
        ["extract", "timeline", "--source", "db"],
        ["stats"],
    ]
    commands = [gbrain_command(args) for args in command_args]
    if any(cmd is None for cmd in commands):
        return [{"cmd": "gbrain", "ok": True, "skipped": True, "stdout": "GBRAIN_SKIPPED"}]
    results = []
    try:
        with gbrain_lock():
            for cmd in commands:
                assert cmd is not None
                result = subprocess.run(cmd, text=True, capture_output=True, check=False, timeout=300, env=gbrain_env())
                results.append({
                    "cmd": " ".join(cmd),
                    "ok": result.returncode == 0,
                    "returncode": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                })
    except TimeoutError as exc:
        results.append({"cmd": "gbrain maintenance", "ok": False, "reason": str(exc)})
    except subprocess.TimeoutExpired as exc:
        results.append({
            "cmd": "gbrain maintenance",
            "ok": False,
            "reason": f"Command timed out after {exc.timeout} seconds",
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
        })
    return results


if __name__ == "__main__":
    for result in run_maintenance():
        print(result)
