#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from common import (
    FORMAL_NOTE_DIRS,
    PROCESSED_DIR,
    STAGING_DIR,
    MAX_FILE_BYTES,
    iter_markdown,
    is_system_note,
    move_or_copy,
    note_exists_for_source_or_hash,
    options_from_args,
    parse_common,
    preflight,
    read_text,
    route_for,
    slug_title,
    split_frontmatter,
    write_text,
)


def update_status(text: str) -> str:
    fm, body = split_frontmatter(text)
    fm["status"] = "processed"
    from common import render_frontmatter

    title = body if body.startswith("# ") else f"# {slug_title(Path(str(fm.get('source_file') or 'note')))}\n\n{body}"
    return render_frontmatter(fm) + title.lstrip()


def main() -> int:
    parser = parse_common("Route staged Obsidian notes into entity folders.")
    args = parser.parse_args()
    opts = options_from_args(args)
    preflight(opts)

    staging = opts.vault / STAGING_DIR
    count = 0
    skipped = 0
    for src in iter_markdown(staging, opts.limit):
        if is_system_note(src):
            if opts.verbose:
                print(f"SKIP system note: {src}")
            skipped += 1
            continue
        if src.stat().st_size > MAX_FILE_BYTES:
            print(f"SKIP large file: {src}")
            continue
        text = read_text(src)
        fm, _ = split_frontmatter(text)
        source_file = str(fm.get("source_file") or "")
        digest = str(fm.get("content_hash") or "")
        existing = note_exists_for_source_or_hash(opts.vault, source_file, digest, FORMAL_NOTE_DIRS)
        if existing:
            if opts.verbose:
                print(f"SKIP already routed: {src} -> {existing}")
            skipped += 1
            continue
        target_dir = opts.vault / route_for(fm)
        dest = target_dir / src.name
        write_text(dest, update_status(text), opts, "route_staging")
        raw_ref = fm.get("source_file")
        if isinstance(raw_ref, str) and raw_ref:
            raw_path = opts.vault / raw_ref
            if raw_path.exists():
                move_or_copy(raw_path, opts.vault / PROCESSED_DIR / raw_path.name, opts, move=False)
        count += 1
    print(f"Routed staging files: {count}; skipped existing/system: {skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
