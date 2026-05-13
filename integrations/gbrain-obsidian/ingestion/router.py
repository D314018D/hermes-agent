import re
from datetime import datetime
from pathlib import Path
from .schema import NoteType

DIR_MAP = {
    "inbox": "00-inbox",
    "person": "01-people",
    "company": "02-companies",
    "project": "03-projects",
    "meeting": "04-meetings",
    "decision": "05-decisions",
    "document": "00-inbox",
}

def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", text)
    text = text.strip("-")
    return text[:80] or "untitled"

def target_path(vault_path: str, note_type: NoteType, title: str, captured_at: str) -> Path:
    date = captured_at[:10] if captured_at else datetime.now().strftime("%Y-%m-%d")
    slug = slugify(title)
    filename = f"{slug}.md" if note_type in ["person", "company", "project"] else f"{date}-{slug}.md"
    return Path(vault_path) / DIR_MAP[note_type] / filename
