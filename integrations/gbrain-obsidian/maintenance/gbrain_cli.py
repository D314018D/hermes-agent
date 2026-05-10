import shutil
import subprocess
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import fcntl


def gbrain_executable() -> str | None:
    found = shutil.which("gbrain")
    if found:
        return found

    candidates = [
        Path.home() / ".bun" / "bin" / "gbrain",
        Path.home() / ".local" / "bin" / "gbrain",
        Path("/opt/homebrew/bin/gbrain"),
        Path("/usr/local/bin/gbrain"),
    ]
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return str(candidate)
    return None


@contextmanager
def gbrain_lock(timeout_seconds: int = 120) -> Iterator[None]:
    lock_dir = Path.home() / ".gbrain"
    lock_dir.mkdir(parents=True, exist_ok=True)
    lock_path = lock_dir / "hermes-gbrain.lock"
    deadline = time.monotonic() + timeout_seconds
    with lock_path.open("w", encoding="utf-8") as lock_file:
        while True:
            try:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise TimeoutError(f"Timed out waiting for Hermes GBrain lock: {lock_path}")
                time.sleep(0.25)
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def run_gbrain_command(
    args: list[str],
    *,
    lock_timeout_seconds: int = 120,
    command_timeout_seconds: int | None = None,
) -> dict:
    gbrain = gbrain_executable()
    if not gbrain:
        return {"ok": False, "skipped": True, "reason": "gbrain not found on PATH"}

    cmd = [gbrain, *args]
    try:
        with gbrain_lock(lock_timeout_seconds):
            result = subprocess.run(
                cmd,
                text=True,
                capture_output=True,
                check=False,
                timeout=command_timeout_seconds,
            )
    except TimeoutError as exc:
        return {"ok": False, "skipped": False, "cmd": " ".join(cmd), "reason": str(exc)}
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "skipped": False,
            "cmd": " ".join(cmd),
            "reason": f"Command timed out after {exc.timeout} seconds",
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
        }

    return {
        "ok": result.returncode == 0,
        "skipped": False,
        "cmd": " ".join(cmd),
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }
