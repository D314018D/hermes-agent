from datetime import datetime, timezone
from pathlib import Path

from .citation_builder import build_citation
from .renderer import key_points
from .schema import IngestInput
from .timeline_appender import append_timeline
from .truth_compiler import compile_truth


REQUIRED_SECTIONS = {
    "project": ["Compiled Truth", "Current Status", "Timeline", "References"],
    "person": ["Compiled Truth", "Relationships", "Timeline", "References"],
    "company": ["Compiled Truth", "Key Contacts", "Projects", "Timeline", "References"],
    "decision": ["Decision", "Reason", "Impact", "Timeline", "References"],
    "meeting": ["Summary", "Attendees", "Actions", "Timeline", "References"],
    "skill": ["Compiled Truth", "Current Status", "Timeline", "References"],
    "inbox": ["Compiled Truth", "Timeline", "References"],
}


def write_brain_page(
    item: IngestInput,
    resolution,
    summary: str,
    entities: list[str],
    tags: list[str],
    relations: list[dict[str, str]] | None = None,
    action_items: list[str] | None = None,
    frontmatter: dict[str, object] | None = None,
    dry_run: bool = False,
) -> str:
    path = Path(resolution.target_path)
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    evidence = key_points(item.content) or [summary]
    citation = build_citation(item)

    if path.exists():
        markdown = path.read_text(encoding="utf-8")
    else:
        markdown = create_page(resolution.target_type, resolution.target_title)

    markdown = update_frontmatter(markdown, resolution.target_type, resolution.target_title, entities, tags, now, frontmatter)
    markdown = ensure_sections(markdown, resolution.target_type)
    markdown = update_section(markdown, "AI Summary", summary)
    if action_items:
        markdown = update_section(markdown, "Action Items", "\n".join(f"- [ ] {item}" for item in action_items))
    if resolution.target_type == "skill" and resolution.target_title == "Current Model Routing":
        compiled_truth = summary
    else:
        compiled_truth = compile_truth(extract_section(markdown, "Compiled Truth"), summary)
    markdown = update_section(markdown, "Compiled Truth", compiled_truth)
    if resolution.target_type in ["project", "skill"]:
        markdown = update_section(markdown, "Current Status", summary)
    if relations:
        markdown = update_section(markdown, "Relations", render_relations(relations))
    markdown = append_timeline(markdown, item, citation, evidence)
    markdown = add_references(markdown, item.attachments)
    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(markdown.rstrip() + "\n", encoding="utf-8")
    return str(path)


def create_page(page_type: str, title: str) -> str:
    sections = REQUIRED_SECTIONS.get(page_type, REQUIRED_SECTIONS["inbox"])
    sections = ["AI Summary", "Action Items", *sections]
    body = "\n\n".join(f"## {section}\n" for section in sections)
    return f"---\n---\n\n# {title}\n\n{body}\n"


def update_frontmatter(
    markdown: str,
    page_type: str,
    title: str,
    entities: list[str],
    tags: list[str],
    updated_at: str,
    extra: dict[str, object] | None = None,
) -> str:
    body = markdown
    if markdown.startswith("---"):
        parts = markdown.split("---", 2)
        if len(parts) == 3:
            body = parts[2].lstrip("\n")
    extra = dict(extra or {})
    lines = [
        "---",
        f"page_type: {page_type}",
        f'title: "{title}"',
        f'created: "{extra.pop("created", updated_at)}"',
        f'updated: "{updated_at}"',
    ]
    for key in [
        "source",
        "status",
        "review_status",
        "top_category",
        "client",
        "project",
        "solution",
        "topic",
        "type",
        "sensitivity",
        "confidence",
        "suggested_folder",
        "final_folder",
    ]:
        if key in extra:
            lines.append(f"{key}: {_yaml_scalar(extra.pop(key))}")
    lines.extend([
        "tags:",
    ])
    lines.extend(f'  - "{tag}"' for tag in sorted(set(tags + [page_type])))
    lines.append("entities:")
    if entities:
        lines.extend(f'  - "{entity}"' for entity in sorted(set(entities)))
    else:
        lines.append("  []")
    lines.append("---")
    return "\n".join(lines) + "\n\n" + body


def _yaml_scalar(value: object) -> str:
    if value is None:
        return '""'
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    escaped = str(value).replace('"', '\\"')
    return f'"{escaped}"'


def ensure_sections(markdown: str, page_type: str) -> str:
    sections = REQUIRED_SECTIONS.get(page_type, REQUIRED_SECTIONS["inbox"])
    text = markdown.rstrip()
    for section in sections:
        if f"## {section}" not in text:
            text += f"\n\n## {section}\n"
    return text + "\n"


def extract_section(markdown: str, section: str) -> str:
    marker = f"## {section}"
    start = markdown.find(marker)
    if start == -1:
        return ""
    content_start = markdown.find("\n", start)
    if content_start == -1:
        return ""
    next_section = markdown.find("\n## ", content_start + 1)
    if next_section == -1:
        return markdown[content_start:].strip()
    return markdown[content_start:next_section].strip()


def update_section(markdown: str, section: str, content: str) -> str:
    marker = f"## {section}"
    start = markdown.find(marker)
    if start == -1:
        return markdown.rstrip() + f"\n\n{marker}\n{content.strip()}\n"
    content_start = markdown.find("\n", start)
    if content_start == -1:
        return markdown.rstrip() + f"\n{content.strip()}\n"
    next_section = markdown.find("\n## ", content_start + 1)
    replacement = f"{marker}\n{content.strip()}\n"
    if next_section == -1:
        return markdown[:start] + replacement
    return markdown[:start] + replacement + markdown[next_section:]


def add_references(markdown: str, attachments: list[str]) -> str:
    if not attachments:
        return markdown
    existing = extract_section(markdown, "References")
    refs = [line.strip() for line in existing.splitlines() if line.strip()]
    for attachment in attachments:
        ref = f"- [[attachments/{attachment}]]"
        if ref not in refs:
            refs.append(ref)
    return update_section(markdown, "References", "\n".join(refs))


def render_relations(relations: list[dict[str, str]]) -> str:
    return "\n".join(
        f"- {relation.get('source', '')} -> {relation.get('target', '')}: {relation.get('type', '')}"
        for relation in relations
    )
