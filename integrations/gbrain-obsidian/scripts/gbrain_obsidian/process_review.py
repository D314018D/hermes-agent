#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from common import (
    FORMAL_NOTE_DIRS,
    REVIEW_DIR,
    STAGING_DIR,
    Options,
    content_hash,
    detect_entities,
    infer_type,
    iter_markdown,
    now_iso,
    note_exists_for_source_or_hash,
    options_from_args,
    parse_common,
    preflight,
    raw_archive_exists,
    read_text,
    render_frontmatter,
    slug_title,
    split_frontmatter,
    wikilink_text,
    write_text,
    MAX_FILE_BYTES,
)


def build_note(src: Path, opts: Options) -> tuple[Path, str]:
    raw = read_text(src)
    existing, body = split_frontmatter(raw)
    entities, alias_candidates = detect_entities(body)
    note_type = str(existing.get("type") or infer_type(body))
    if note_type not in {
        "meeting",
        "project_update",
        "decision",
        "person",
        "company",
        "skill",
        "idea",
        "task",
        "reference",
    }:
        note_type = "reference"

    company = [e for e in entities if e in {"Woolworths", "Hanshow", "Coles", "Bunnings", "Dan Murphy's"}]
    people = [e for e in entities if e in {"Ben", "Rob", "Matt", "Nathan", "Jun", "Umesh", "Penty"}]
    topics = [e for e in entities if e not in company and e not in people]
    project = [e for e in topics if e in {"Smart Trolley", "Lumina", "BuyBoost", "CartWise"}]

    timestamp = now_iso()
    frontmatter = {
        "type": note_type,
        "status": "staging",
        "source": existing.get("source") or "gbrain_review",
        "created": existing.get("created") or timestamp,
        "updated": timestamp,
        "project": project,
        "company": company,
        "people": people,
        "topics": topics,
        "tags": sorted(set(["gbrain-review", note_type.replace("_", "-")])),
        "gbrain_status": existing.get("gbrain_status") or "unknown",
        "embedding_status": existing.get("embedding_status") or "unknown",
        "source_file": str(src.relative_to(opts.vault)),
        "content_hash": content_hash(body),
        "alias_candidates": alias_candidates,
    }

    title = slug_title(src)
    linked_body = wikilink_text(body, entities)
    note = render_frontmatter(frontmatter)
    note += f"# {title}\n\n"
    note += "## Summary\n\n"
    note += "_Pending review._\n\n"
    note += "## Notes\n\n"
    note += linked_body.rstrip() + "\n"
    dest = opts.vault / STAGING_DIR / src.name
    return dest, note


def main() -> int:
    parser = parse_common("Process raw GBrain review notes into Obsidian staging notes.")
    args = parser.parse_args()
    opts = options_from_args(args)
    preflight(opts)

    review = opts.vault / REVIEW_DIR
    processed = 0
    skipped = 0
    for src in iter_markdown(review, opts.limit):
        if src.stat().st_size > MAX_FILE_BYTES:
            print(f"SKIP large file: {src}")
            continue
        raw = read_text(src)
        _, body = split_frontmatter(raw)
        digest = content_hash(body)
        source_file = str(src.relative_to(opts.vault))
        existing = note_exists_for_source_or_hash(
            opts.vault,
            source_file,
            digest,
            [STAGING_DIR, *FORMAL_NOTE_DIRS],
        )
        if existing or raw_archive_exists(opts.vault, src, digest):
            if opts.verbose:
                where = existing if existing else opts.vault / "00_Inbox" / "Processed" / src.name
                print(f"SKIP already processed: {src} -> {where}")
            skipped += 1
            continue
        dest, note = build_note(src, opts)
        write_text(dest, note, opts, "process_review")
        processed += 1
    print(f"Processed review files: {processed}; skipped existing: {skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
