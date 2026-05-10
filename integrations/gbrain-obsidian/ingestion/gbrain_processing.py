from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass, field

from .classifier import Classification, classify_input
from .entities import extract_entities
from .schema import IngestInput
from .scorer import score_input
from .summarizer import summarize_text


@dataclass
class GBrainProcessingResult:
    classification: Classification
    score: int
    summary: str
    entities: list[str]
    action_items: list[str]
    relations: list[dict[str, str]]
    embedding: list[float]
    content_hash: str
    tags: list[str] = field(default_factory=list)
    duplicate_of: str | None = None


def process_with_gbrain(item: IngestInput, existing_hashes: set[str] | None = None) -> GBrainProcessingResult:
    """Run the durable-memory processing stage before rendering Markdown."""
    text = f"{item.title}\n\n{item.content}"
    classification = classify_input(item)
    score = score_input(item)
    summary = summarize_text(item.content)
    entities = extract_entities(text)
    content_hash = _content_hash(item)
    duplicate_of = content_hash if content_hash in (existing_hashes or set()) else None
    return GBrainProcessingResult(
        classification=classification,
        score=score,
        summary=summary,
        entities=entities,
        action_items=extract_action_items(item.content),
        relations=extract_relations(entities, item.content),
        embedding=build_embedding(text),
        content_hash=content_hash,
        tags=[classification.note_type, item.source_type],
        duplicate_of=duplicate_of,
    )


def extract_relations(entities: list[str], text: str) -> list[dict[str, str]]:
    relations: list[dict[str, str]] = []
    clean = " ".join(text.split())
    for left_index, left in enumerate(entities):
        for right in entities[left_index + 1:]:
            if left == right:
                continue
            if left.lower() in clean.lower() and right.lower() in clean.lower():
                relations.append({
                    "source": left,
                    "target": right,
                    "type": "co_mentioned",
                })
    return relations


def extract_action_items(text: str) -> list[str]:
    actions: list[str] = []
    patterns = [
        r"(?:next step|action|todo|follow up|need to|needs to|must|confirm|review|send|prepare)[:：]?\s*([^。.!?\n]+)",
        r"(?:下一步|需要|确认|跟进|准备|发送|复查)[:：]?\s*([^。.!?\n]+)",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            action = " ".join(match.group(1).split()).strip(" -:：")
            if action and action not in actions:
                actions.append(action)
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(("- [ ]", "* [ ]")):
            action = stripped[5:].strip()
            if action and action not in actions:
                actions.append(action)
    return actions[:10]


def build_embedding(text: str, dimensions: int = 16) -> list[float]:
    """Deterministic lightweight embedding placeholder for local smoke tests."""
    buckets = [0.0 for _ in range(dimensions)]
    tokens = re.findall(r"[\w\u4e00-\u9fff]+", text.lower())
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = digest[0] % dimensions
        buckets[index] += 1.0
    norm = math.sqrt(sum(value * value for value in buckets)) or 1.0
    return [round(value / norm, 6) for value in buckets]


def _content_hash(item: IngestInput) -> str:
    body = "\n".join([
        item.source_type,
        item.source_app,
        item.title.strip(),
        item.content.strip(),
        "\n".join(item.attachments),
    ])
    return hashlib.sha256(body.encode("utf-8")).hexdigest()
