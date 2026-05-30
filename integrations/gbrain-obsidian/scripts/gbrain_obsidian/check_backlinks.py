#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

from common import (
    MOC_TARGETS,
    SYSTEM_NOTE_STEMS,
    is_attachment_target,
    is_system_note,
    iter_markdown,
    options_from_args,
    parse_common,
    preflight,
    read_text,
    write_text,
)

LINK_RE = re.compile(r"\[\[([^\]|#]+)")


def main() -> int:
    parser = parse_common("Check broken wikilinks, orphan notes, and missing entity pages.")
    args = parser.parse_args()
    opts = options_from_args(args)
    preflight(opts)

    files: list[Path] = []
    for folder in ["00_Inbox", "01-people", "02-companies", "03-projects", "04-meetings", "05-decisions", "06-skills"]:
        files.extend(iter_markdown(opts.vault / folder, opts.limit * 20))
    files = [path for path in files if not is_system_note(path)]

    stems = {p.stem for p in files}
    incoming: dict[str, int] = {p.stem: 0 for p in files}
    broken: set[str] = set()
    missing_entities: list[str] = []

    for path in files:
        text = read_text(path)
        for target in LINK_RE.findall(text):
            if target in SYSTEM_NOTE_STEMS or is_attachment_target(target):
                continue
            if target in incoming:
                incoming[target] += 1
            elif target not in stems:
                broken.add(f"{path.relative_to(opts.vault)} -> [[{target}]]")

    for entity, rel in MOC_TARGETS.items():
        if not (opts.vault / rel).exists():
            missing_entities.append(f"{entity}: {rel}")

    orphans = [name for name, count in incoming.items() if count == 0 and name not in MOC_TARGETS]
    report = [
        "# GBrain Obsidian Backlink Report",
        "",
        "## Broken Links",
        *(f"- {item}" for item in sorted(broken)[:200]),
        "",
        "## Orphan Notes",
        *(f"- [[{item}]]" for item in sorted(orphans)[:200]),
        "",
        "## Missing Entity Pages",
        *(f"- {item}" for item in sorted(missing_entities)),
        "",
    ]
    output = "\n".join(report)
    report_path = opts.vault / "00_Inbox" / "Gbrain_Staging" / "gbrain-backlink-report.md"
    if opts.write:
        write_text(report_path, output, opts, "check_backlinks")
    else:
        print(output)
    print(f"Broken links: {len(broken)}; orphans: {len(orphans)}; missing entity pages: {len(missing_entities)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
