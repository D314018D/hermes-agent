from .schema import IngestInput


def append_timeline(markdown: str, item: IngestInput, citation: str, evidence: list[str]) -> str:
    if "## Timeline" not in markdown:
        markdown = markdown.rstrip() + "\n\n## Timeline\n"

    date = item.captured_at[:10] if item.captured_at else "undated"
    heading = f"### {date} — {item.source_app}/{item.source_type}"
    bullets = evidence or [item.title]
    entry = [heading, "", f"Source: {citation}", ""]
    entry.extend(f"- {bullet}" for bullet in bullets if bullet)
    entry_text = "\n".join(entry).rstrip() + "\n"

    marker = "## Timeline"
    index = markdown.find(marker)
    after_marker = index + len(marker)
    next_section = markdown.find("\n## ", after_marker)
    if next_section == -1:
        return markdown.rstrip() + "\n\n" + entry_text
    return markdown[:next_section].rstrip() + "\n\n" + entry_text + "\n" + markdown[next_section:].lstrip("\n")

