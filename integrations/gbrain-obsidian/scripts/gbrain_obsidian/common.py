#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_VAULT = ROOT / "obsidian-vault"
LOG_DIR = ROOT / "logs" / "gbrain_obsidian"
BACKUP_DIR = LOG_DIR / "backups"

REVIEW_DIR = Path("00_Inbox/Gbrain_Review")
STAGING_DIR = Path("00_Inbox/Gbrain_Staging")
PROCESSED_DIR = Path("00_Inbox/Processed")
FORMAL_NOTE_DIRS = [
    Path("01-people"),
    Path("02-companies"),
    Path("03-projects"),
    Path("04-meetings"),
    Path("05-decisions"),
    Path("06-skills"),
]

MAX_FILE_BYTES = 1024 * 1024
DEFAULT_LIMIT = 20
SYSTEM_NOTE_NAMES = {
    "gbrain-backlink-report.md",
}
SYSTEM_NOTE_STEMS = {Path(name).stem for name in SYSTEM_NOTE_NAMES}
ATTACHMENT_PREFIXES = ("attachments/",)

VALID_TYPES = {
    "meeting",
    "project_update",
    "decision",
    "person",
    "company",
    "skill",
    "idea",
    "task",
    "reference",
}

ENTITY_ALIASES = {
    "Woolworths": ["Woolworths", "沃尔沃斯", "伍尔沃斯", "沃尔斯"],
    "Hanshow": ["Hanshow"],
    "Coles": ["Coles"],
    "Bunnings": ["Bunnings"],
    "Dan Murphy's": ["Dan Murphy's", "Dan Murphys"],
    "Smart Trolley": ["Smart Trolley", "smart trolley", "智能购物车"],
    "NFC": ["NFC"],
    "Firmware": ["Firmware", "firmware", "固件"],
    "ESL": ["ESL"],
    "Lumina": ["Lumina"],
    "BuyBoost": ["BuyBoost"],
    "CartWise": ["CartWise"],
    "GBrain": ["GBrain", "gbrain"],
    "Hermes": ["Hermes"],
    "oMLX": ["oMLX", "omlx", "OMLX"],
    "Ben": ["Ben"],
    "Rob": ["Rob"],
    "Matt": ["Matt"],
    "Nathan": ["Nathan"],
    "Jun": ["Jun"],
    "Umesh": ["Umesh"],
    "Penty": ["Penty"],
}

MOC_TARGETS = {
    "Woolworths": Path("02-companies/Woolworths.md"),
    "Hanshow": Path("02-companies/Hanshow.md"),
    "Smart Trolley": Path("03-projects/Smart Trolley.md"),
    "Ben": Path("01-people/Ben.md"),
    "Rob": Path("01-people/Rob.md"),
    "Jun": Path("01-people/Jun.md"),
    "NFC": Path("06-skills/NFC.md"),
    "Firmware": Path("06-skills/Firmware.md"),
    "ESL": Path("06-skills/ESL.md"),
    "GBrain": Path("06-skills/GBrain.md"),
    "Hermes": Path("06-skills/Hermes.md"),
    "oMLX": Path("06-skills/oMLX.md"),
}


@dataclass
class Options:
    vault: Path
    write: bool
    limit: int
    verbose: bool


def parse_common(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Preview changes without writing files.")
    mode.add_argument("--write", action="store_true", help="Write changes to the vault.")
    parser.add_argument("--vault", default=str(DEFAULT_VAULT), help="Obsidian vault path.")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help="Maximum files to process.")
    parser.add_argument("--verbose", action="store_true", help="Print detailed actions.")
    return parser


def options_from_args(args: argparse.Namespace) -> Options:
    return Options(
        vault=Path(args.vault).expanduser().resolve(),
        write=bool(args.write),
        limit=max(1, int(args.limit)),
        verbose=bool(args.verbose),
    )


def ensure_inside_vault(vault: Path, path: Path) -> Path:
    resolved = path.expanduser().resolve()
    root = vault.expanduser().resolve()
    if resolved != root and root not in resolved.parents:
        raise ValueError(f"path escapes vault: {resolved}")
    return resolved


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def slug_title(path: Path) -> str:
    title = path.stem.replace("_", " ").replace("-", " ")
    title = re.sub(r"\s+", " ", title).strip()
    return title or path.stem


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def is_markdown(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() == ".md" and path.name != ".gitkeep"


def is_system_note(path: Path) -> bool:
    return path.name in SYSTEM_NOTE_NAMES


def iter_markdown(folder: Path, limit: int) -> Iterable[Path]:
    if not folder.exists():
        return []
    files = [p for p in sorted(folder.iterdir()) if is_markdown(p)]
    return files[:limit]


def iter_markdown_all(folder: Path) -> Iterable[Path]:
    if not folder.exists():
        return []
    return [p for p in sorted(folder.iterdir()) if is_markdown(p)]


def split_frontmatter(text: str) -> tuple[dict[str, object], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end < 0:
        return {}, text
    raw = text[4:end].strip()
    body = text[end + 4 :].lstrip("\n")
    data: dict[str, object] = {}
    for line in raw.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            items = [v.strip().strip("\"'") for v in value[1:-1].split(",") if v.strip()]
            data[key] = items
        else:
            data[key] = value.strip("\"'")
    return data, body


def render_frontmatter(data: dict[str, object]) -> str:
    lines = ["---"]
    for key in [
        "type",
        "status",
        "source",
        "created",
        "updated",
        "project",
        "company",
        "people",
        "topics",
        "tags",
        "gbrain_status",
        "embedding_status",
        "source_file",
        "content_hash",
        "alias_candidates",
    ]:
        value = data.get(key, "")
        if isinstance(value, list):
            escaped = ", ".join(json.dumps(v, ensure_ascii=False) for v in value)
            lines.append(f"{key}: [{escaped}]")
        else:
            lines.append(f"{key}: {json.dumps(value, ensure_ascii=False) if value else ''}")
    lines.append("---")
    return "\n".join(lines) + "\n\n"


def detect_entities(text: str) -> tuple[list[str], list[str]]:
    found: list[str] = []
    alias_candidates: list[str] = []
    lowered = text.lower()
    for canonical, aliases in ENTITY_ALIASES.items():
        matched_aliases = []
        for alias in aliases:
            if alias.isascii():
                if re.search(rf"(?<![\w]){re.escape(alias)}(?![\w])", text, flags=re.IGNORECASE):
                    matched_aliases.append(alias)
            elif alias in text:
                matched_aliases.append(alias)
        if matched_aliases:
            found.append(canonical)
            for alias in matched_aliases:
                if alias != canonical and alias.lower() != canonical.lower():
                    alias_candidates.append(f"{alias}=>{canonical}")
        elif canonical.lower() in lowered:
            found.append(canonical)
    return sorted(set(found)), sorted(set(alias_candidates))


def wikilink_text(text: str, entities: list[str]) -> str:
    result = text
    for entity in sorted(entities, key=len, reverse=True):
        if f"[[{entity}]]" in result:
            continue
        aliases = ENTITY_ALIASES.get(entity, [entity])
        for alias in sorted(aliases, key=len, reverse=True):
            if not alias.isascii() and alias != entity:
                continue
            pattern = re.compile(rf"(?<![\[\w])({re.escape(alias)})(?![\]\w])", re.IGNORECASE)
            result, count = pattern.subn(f"[[{entity}]]", result, count=1)
            if count:
                break
    return result


def infer_type(text: str) -> str:
    lower = text.lower()
    if any(w in lower for w in ["meeting", "会议", "纪要", "operation meeting"]):
        return "meeting"
    if any(w in lower for w in ["decision", "决定", "确定"]):
        return "decision"
    if any(w in lower for w in ["project", "项目", "进展", "预算"]):
        return "project_update"
    if any(w in lower for w in ["nfc", "firmware", "esl", "技能", "技术"]):
        return "skill"
    if any(w in lower for w in ["task", "todo", "待办", "下一步"]):
        return "task"
    return "reference"


def route_for(frontmatter: dict[str, object]) -> Path:
    note_type = str(frontmatter.get("type") or "reference")
    company = _first(frontmatter.get("company"))
    project = _first(frontmatter.get("project"))
    people = _first(frontmatter.get("people"))
    topics = _list(frontmatter.get("topics"))
    if note_type == "decision":
        return Path("05-decisions")
    if note_type == "meeting":
        return Path("04-meetings")
    if note_type == "skill" or any(t in {"NFC", "Firmware", "ESL", "GBrain", "Hermes", "oMLX"} for t in topics):
        return Path("06-skills")
    if note_type == "project_update" or project:
        return Path("03-projects")
    if note_type == "company" or company:
        return Path("02-companies")
    if note_type == "person" or (people and not company and not project and not topics):
        return Path("01-people")
    return Path("00_Inbox/Processed")


def note_exists_for_source_or_hash(vault: Path, source_file: str, digest: str, folders: Iterable[Path]) -> Path | None:
    for folder in folders:
        for path in iter_markdown_all(vault / folder):
            if is_system_note(path) or path.stat().st_size > MAX_FILE_BYTES:
                continue
            fm, _ = split_frontmatter(read_text(path))
            if digest and fm.get("content_hash") == digest:
                return path
            if source_file and fm.get("source_file") == source_file:
                return path
    return None


def raw_archive_exists(vault: Path, source: Path, digest: str) -> bool:
    archived = vault / PROCESSED_DIR / source.name
    if not archived.exists() or not archived.is_file():
        return False
    _, body = split_frontmatter(read_text(archived))
    return content_hash(body) == digest


def is_attachment_target(target: str) -> bool:
    normalized = target.strip().lstrip("/")
    return normalized.startswith(ATTACHMENT_PREFIXES)


def _list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(v) for v in value if str(v)]
    if isinstance(value, str) and value:
        return [value]
    return []


def _first(value: object) -> str:
    values = _list(value)
    return values[0] if values else ""


def backup_file(path: Path, vault: Path) -> Path:
    rel = path.resolve().relative_to(vault.resolve())
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = BACKUP_DIR / stamp / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, dest)
    return dest


def write_text(path: Path, text: str, opts: Options, action: str) -> None:
    ensure_inside_vault(opts.vault, path)
    if path.exists() and read_text(path) == text:
        print(f"SKIP unchanged {action}: {path}")
        return
    if not opts.write:
        print(f"DRY-RUN {action}: {path}")
        return
    if path.exists():
        backup_file(path, opts.vault)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    log_event({"action": action, "path": str(path), "ts": now_iso()})
    print(f"WROTE {action}: {path}")


def move_or_copy(src: Path, dest: Path, opts: Options, *, move: bool = False) -> None:
    ensure_inside_vault(opts.vault, src)
    ensure_inside_vault(opts.vault, dest)
    op = "MOVE" if move else "COPY"
    if not opts.write:
        print(f"DRY-RUN {op}: {src} -> {dest}")
        return
    if src.exists():
        backup_file(src, opts.vault)
    if dest.exists():
        backup_file(dest, opts.vault)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if move:
        shutil.move(str(src), str(dest))
    else:
        shutil.copy2(src, dest)
    log_event({"action": op.lower(), "src": str(src), "dest": str(dest), "ts": now_iso()})
    print(f"{op}: {src} -> {dest}")


def log_event(event: dict[str, object]) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with (LOG_DIR / "actions.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def preflight(opts: Options, *, require_space_gb: int = 10) -> None:
    if opts.limit <= 0:
        raise SystemExit("--limit must be positive")
    if not opts.vault.exists():
        raise SystemExit(f"vault not found: {opts.vault}")
    try:
        load_1m, _, _ = os.getloadavg()
        if load_1m > 8.0:
            raise SystemExit(f"system load is high ({load_1m:.2f}); skipping")
    except OSError:
        pass
    usage = shutil.disk_usage(opts.vault)
    if opts.write and usage.free < require_space_gb * 1024**3:
        raise SystemExit(f"free disk space below {require_space_gb}GB; refusing writes")


def gbrain_process_running() -> bool:
    try:
        result = subprocess.run(
            ["ps", "axo", "command"],
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError:
        return False
    needle_re = re.compile(r"\bgbrain\b.*\bembed\b|gbrain_maintain\.py|embed --stale")
    current = str(os.getpid())
    for line in result.stdout.splitlines():
        if current in line:
            continue
        if needle_re.search(line):
            return True
    return False


def run_gbrain(args: list[str], *, dry_run: bool = False, timeout_seconds: int = 300) -> int:
    if gbrain_process_running():
        print("SKIP gbrain command: another GBrain maintenance process appears to be running")
        return 0
    cmd = ["gbrain", *args]
    if dry_run and args[:1] == ["extract"] and "--dry-run" not in cmd:
        cmd.append("--dry-run")
    with hermes_gbrain_lock(timeout_seconds=2):
        print("RUN " + " ".join(cmd), flush=True)
        result = subprocess.run(cmd, text=True, check=False, timeout=timeout_seconds)
    return int(result.returncode)


@contextmanager
def hermes_gbrain_lock(timeout_seconds: int = 1):
    import fcntl
    import time

    lock_path = Path.home() / ".gbrain" / "hermes-gbrain.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + timeout_seconds
    with lock_path.open("w", encoding="utf-8") as handle:
        while True:
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise TimeoutError(f"Timed out waiting for {lock_path}")
                time.sleep(0.25)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
