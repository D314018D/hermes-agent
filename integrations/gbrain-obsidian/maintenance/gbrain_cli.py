import os
import shutil
import subprocess
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import fcntl


def bun_executable() -> str | None:
    found = shutil.which("bun")
    if found:
        return found

    # Launchd/Hermes can run with a narrow PATH. Prefer the real Bun runtime
    # locations so a gbrain shim with #!/usr/bin/env bun still works.
    candidates = [
        Path.home() / ".local" / "bin" / "bun",
        Path.home() / ".bun" / "bin" / "bun",
        Path("/opt/homebrew/bin/bun"),
        Path("/usr/local/bin/bun"),
    ]
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return str(candidate)
    return None


def _is_usable_gbrain_candidate(candidate: Path) -> bool:
    if not (candidate.exists() and candidate.is_file()):
        return False
    if candidate.parent == Path.home() / ".bun" / "bin":
        colocated_bun = candidate.parent / "bun"
        if not colocated_bun.exists():
            return False
    return True


def gbrain_executable() -> str | None:
    found = shutil.which("gbrain")
    if found:
        return found

    candidates = [
        Path.home() / ".local" / "bin" / "gbrain",
        Path.home() / ".bun" / "bin" / "gbrain",
        Path("/opt/homebrew/bin/gbrain"),
        Path("/usr/local/bin/gbrain"),
    ]
    for candidate in candidates:
        if _is_usable_gbrain_candidate(candidate):
            return str(candidate)
    return None


def _requires_bun(script_path: str) -> bool:
    try:
        with open(script_path, "r", encoding="utf-8") as handle:
            first_line = handle.readline(200)
    except OSError:
        return False
    return "env bun" in first_line or first_line.rstrip().endswith("/bun")


def gbrain_command(args: list[str]) -> list[str] | None:
    gbrain = gbrain_executable()
    if not gbrain:
        return None
    if _requires_bun(gbrain):
        bun = bun_executable()
        if not bun:
            return None
        return [bun, gbrain, *args]
    return [gbrain, *args]


def gbrain_env() -> dict[str, str]:
    env = os.environ.copy()
    bun = bun_executable()
    if bun:
        bun_dir = str(Path(bun).parent)
        current_path = env.get("PATH", "")
        path_parts = [part for part in current_path.split(os.pathsep) if part]
        if bun_dir not in path_parts:
            env["PATH"] = os.pathsep.join([bun_dir, *path_parts])
    return env


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
    cmd = gbrain_command(args)
    if not cmd:
        gbrain = gbrain_executable()
        if gbrain and _requires_bun(gbrain) and not bun_executable():
            return {"ok": False, "skipped": True, "reason": f"bun not found for bun-based gbrain executable: {gbrain}"}
        return {"ok": False, "skipped": True, "reason": "gbrain not found on PATH"}

    try:
        with gbrain_lock(lock_timeout_seconds):
            result = subprocess.run(
                cmd,
                text=True,
                capture_output=True,
                check=False,
                timeout=command_timeout_seconds,
                env=gbrain_env(),
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
