import subprocess

from .gbrain_cli import gbrain_executable, gbrain_lock


def run_maintenance() -> list[dict]:
    gbrain = gbrain_executable()
    if not gbrain:
        return [{"cmd": "gbrain", "ok": True, "skipped": True, "stdout": "GBRAIN_SKIPPED"}]
    commands = [
        [gbrain, "embed", "--stale"],
        [gbrain, "extract", "links", "--source", "db"],
        [gbrain, "extract", "timeline", "--source", "db"],
        [gbrain, "stats"],
    ]
    results = []
    try:
        with gbrain_lock():
            for cmd in commands:
                result = subprocess.run(cmd, text=True, capture_output=True, check=False, timeout=300)
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
