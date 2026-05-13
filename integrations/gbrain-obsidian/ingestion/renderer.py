import re

from .schema import IngestInput, NoteType
from .entities import extract_entities
from .summarizer import summarize_text

def yaml_value(value: str) -> str:
    escaped = str(value).replace('"', '\\"')
    return f'"{escaped}"'

def bullet_list(values: list[str]) -> str:
    return "\n".join([f"  - {yaml_value(value)}" for value in values]) or "  []"

def key_points(text: str) -> list[str]:
    clean = " ".join(text.split())
    sentences = re.split(r"(?<=[。！？!?])\s*|(?<!\d)\.(?!\d)\s+", clean)
    return [sentence for sentence in sentences if sentence][:5]

def render_markdown(
    item: IngestInput,
    note_type: NoteType,
    score: int,
    save_raw: bool = False,
    summary: str | None = None,
    entities: list[str] | None = None,
    tags: list[str] | None = None,
    relations: list[dict[str, str]] | None = None,
) -> tuple[str, str, list[str], list[str]]:
    text = f"{item.title}\n\n{item.content}"
    entities = entities if entities is not None else extract_entities(text)
    summary = summary if summary is not None else summarize_text(item.content)
    tags = tags if tags is not None else [note_type, item.source_type]

    frontmatter_entities = bullet_list(entities)
    frontmatter_tags = bullet_list(tags)
    frontmatter_attachments = bullet_list(item.attachments)
    points = key_points(item.content)
    rendered_points = "\n".join([f"- {point}" for point in points]) or "- No key points extracted."
    metadata_lines = "\n".join(
        [f"- **{key}**: {value}" for key, value in sorted(item.metadata.items()) if value]
    )

    md = f"""---
type: {note_type}
source_type: {yaml_value(item.source_type)}
source_app: {yaml_value(item.source_app)}
captured_at: {yaml_value(item.captured_at)}
score: {score}
tags:
{frontmatter_tags}
entities:
{frontmatter_entities}
attachments:
{frontmatter_attachments}
---

# {item.title}

## Summary
{summary}

## Key Points
{rendered_points}

## Actions
- Review and enrich this note if it becomes durable knowledge.

## References
"""

    for att in item.attachments:
        md += f"- [[attachments/{att}]]\n"

    if metadata_lines:
        md += f"\n## Source Metadata\n{metadata_lines}\n"

    if relations:
        md += "\n## Relations\n"
        for relation in relations:
            md += f"- {relation.get('source', '')} -> {relation.get('target', '')}: {relation.get('type', '')}\n"

    if save_raw:
        md += f"\n## Raw Content\n{item.content}\n"

    return md, summary, entities, tags
