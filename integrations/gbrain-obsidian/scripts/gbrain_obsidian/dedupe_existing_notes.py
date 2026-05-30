#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from common import (
    FORMAL_NOTE_DIRS,
    MAX_FILE_BYTES,
    PROCESSED_DIR,
    STAGING_DIR,
    content_hash,
    is_system_note,
    iter_markdown_all,
    move_or_copy,
    options_from_args,
    parse_common,
    preflight,
    read_text,
    route_for,
    split_frontmatter,
)

STAGING_DEDUPED_DIR = STAGING_DIR / "_deduped"
FORMAL_DEDUPED_DIR = PROCESSED_DIR / "_deduped_formal"


@dataclass
class NoteRecord:
    path: Path
    folder: Path
    source_file: str
    digest: str
    body: str
    frontmatter: dict[str, object]


def collect_notes(vault: Path, folders: list[Path]) -> list[NoteRecord]:
    records: list[NoteRecord] = []
    for folder in folders:
        for path in iter_markdown_all(vault / folder):
            if is_system_note(path):
                continue
            if path.stat().st_size > MAX_FILE_BYTES:
                print(f"SKIP large file: {path}")
                continue
            text = read_text(path)
            fm, body = split_frontmatter(text)
            digest = str(fm.get("content_hash") or content_hash(body))
            source_file = str(fm.get("source_file") or "")
            records.append(NoteRecord(path, folder, source_file, digest, body, fm))
    return records


def key_for(record: NoteRecord) -> tuple[str, str]:
    return record.source_file, record.digest


def has_same_source_or_hash(record: NoteRecord, candidates: list[NoteRecord]) -> bool:
    for candidate in candidates:
        if record.source_file and record.source_file == candidate.source_file:
            return True
        if record.digest and record.digest == candidate.digest:
            return True
    return False


def canonical_formal(records: list[NoteRecord]) -> NoteRecord:
    def score(record: NoteRecord) -> tuple[int, str]:
        expected = route_for(record.frontmatter)
        folder_score = 0 if record.folder == expected else 1
        return folder_score, str(record.path)

    return sorted(records, key=score)[0]


def main() -> int:
    parser = parse_common("Deduplicate existing Obsidian helper markdown files.")
    args = parser.parse_args()
    opts = options_from_args(args)
    preflight(opts)

    formal = collect_notes(opts.vault, FORMAL_NOTE_DIRS)
    staging = collect_notes(opts.vault, [STAGING_DIR])

    moved_staging = 0
    moved_formal = 0
    skipped = 0

    for record in staging[: opts.limit]:
        if has_same_source_or_hash(record, formal):
            dest = opts.vault / STAGING_DEDUPED_DIR / record.path.name
            move_or_copy(record.path, dest, opts, move=True)
            moved_staging += 1
        else:
            skipped += 1

    grouped: dict[tuple[str, str], list[NoteRecord]] = {}
    for record in formal:
        grouped.setdefault(key_for(record), []).append(record)

    for records in grouped.values():
        if len(records) < 2:
            continue
        keep = canonical_formal(records)
        for record in records:
            if record.path == keep.path:
                continue
            if record.body != keep.body:
                print(f"REPORT ambiguous duplicate, kept both: {record.path} vs {keep.path}")
                skipped += 1
                continue
            dest = opts.vault / FORMAL_DEDUPED_DIR / record.path.relative_to(opts.vault)
            move_or_copy(record.path, dest, opts, move=True)
            moved_formal += 1

    print(
        "Deduped notes: "
        f"staging moved={moved_staging}; formal moved={moved_formal}; skipped/reported={skipped}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
