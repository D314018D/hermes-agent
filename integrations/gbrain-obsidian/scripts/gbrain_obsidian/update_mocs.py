#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from common import (
    FORMAL_NOTE_DIRS,
    MOC_TARGETS,
    SYSTEM_NOTE_STEMS,
    detect_entities,
    iter_markdown,
    is_system_note,
    options_from_args,
    parse_common,
    preflight,
    read_text,
    split_frontmatter,
    write_text,
)

SECTIONS = [
    "Overview",
    "Related Notes",
    "Meetings",
    "Decisions",
    "Projects",
    "People",
    "Topics",
]


def ensure_moc(entity: str, existing: str) -> str:
    text = existing.strip() if existing.strip() else f"# {entity}\n"
    if not text.startswith("# "):
        text = f"# {entity}\n\n{text}"
    for section in SECTIONS:
        marker = f"## {section}"
        if marker not in text:
            text = text.rstrip() + f"\n\n{marker}\n"
    return text.rstrip() + "\n"


def add_related(text: str, link: str) -> str:
    marker = "## Related Notes"
    if f"- {link}" in text:
        return text
    idx = text.find(marker)
    if idx < 0:
        return text.rstrip() + f"\n\n{marker}\n- {link}\n"
    next_idx = text.find("\n## ", idx + len(marker))
    insert_at = next_idx if next_idx >= 0 else len(text)
    before = text[:insert_at].rstrip()
    after = text[insert_at:]
    return before + f"\n- {link}\n" + after


def remove_system_links(text: str) -> str:
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if any(stripped == f"- [[{stem}]]" for stem in SYSTEM_NOTE_STEMS):
            continue
        lines.append(line)
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = parse_common("Update Obsidian MOC pages with related note links.")
    args = parser.parse_args()
    opts = options_from_args(args)
    preflight(opts)

    notes = []
    for folder in FORMAL_NOTE_DIRS:
        notes.extend(iter_markdown(opts.vault / folder, opts.limit * 10))

    originals: dict[str, str] = {}
    updates: dict[str, str] = {}
    for entity, rel in MOC_TARGETS.items():
        moc_path = opts.vault / rel
        if not moc_path.exists():
            continue
        original = read_text(moc_path)
        originals[entity] = original
        current = ensure_moc(entity, original)
        cleaned = remove_system_links(current)
        if cleaned != original:
            updates[entity] = cleaned

    for note in notes:
        if is_system_note(note):
            continue
        if note.name in {path.name for path in MOC_TARGETS.values()}:
            continue
        text = read_text(note)
        _, body = split_frontmatter(text)
        entities, _ = detect_entities(body)
        link = f"[[{note.stem}]]"
        for entity in entities:
            if entity not in MOC_TARGETS:
                continue
            moc_path = opts.vault / MOC_TARGETS[entity]
            current = updates.get(entity)
            if current is None:
                current = read_text(moc_path) if moc_path.exists() else ""
                current = ensure_moc(entity, current)
            updates[entity] = add_related(current, link)

    changed = 0
    for entity, text in updates.items():
        if originals.get(entity) == text:
            continue
        write_text(opts.vault / MOC_TARGETS[entity], text, opts, "update_moc")
        changed += 1
    print(f"MOC pages updated: {changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
