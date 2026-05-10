from dataclasses import dataclass
from pathlib import Path

from .gbrain_processing import build_embedding
from .memory_store import load_memory_embeddings, load_memory_records
from .router import slugify
from .schema import IngestInput


@dataclass
class PageResolution:
    target_type: str
    target_title: str
    target_path: str
    confidence: float
    reason: str


PROJECT_ALIASES = {
    "Woolworths N70 Robot Test Unit": [
        "n70",
        "n70 robot",
        "large robot test unit",
        "robot test unit",
        "woolworths robot pilot",
        "woolworths n70",
        "大机器人测试机",
    ]
}

PROJECT_KEYWORDS = ["project", "pilot", "poc", "trial", "rollout", "deployment", "test unit", "测试机"]
COMPANY_NAMES = ["woolworths", "hanshow", "coles", "bunnings"]
MODEL_ROUTING_KEYWORDS = [
    "model", "chatgpt", "chatgtp", "qwen", "hermes", "router", "routing",
    "模型", "路由", "当前使用", "现在用的模型"
]
MEETING_KEYWORDS = [
    "meeting", "meetings", "call", "workshop", "discussion", "minutes",
    "会议", "会谈", "纪要", "讨论", "截图",
]


def resolve_page(item: IngestInput, vault_path: str = "./obsidian-vault") -> PageResolution:
    text = f"{item.title}\n{item.content}".lower()
    vault = Path(vault_path)
    learned = _learned_route(item, vault)
    if learned is not None:
        return learned

    if "n70" in text and "woolworths" in text:
        return _project(vault, "Woolworths N70 Robot Test Unit", 0.98, "matched N70 and Woolworths")

    if any(keyword in text for keyword in MODEL_ROUTING_KEYWORDS):
        path = vault / "06-skills" / "current-model-routing.md"
        return PageResolution(
            target_type="skill",
            target_title="Current Model Routing",
            target_path=str(path),
            confidence=0.9,
            reason="matched model routing/configuration keyword",
        )

    for project, aliases in PROJECT_ALIASES.items():
        if any(alias.lower() in text for alias in aliases):
            return _project(vault, project, 0.9, f"matched known project alias for {project}")

    if any(keyword in text for keyword in MEETING_KEYWORDS):
        date = item.captured_at[:10] if item.captured_at else "undated"
        title = item.title
        path = vault / "04-meetings" / f"{date}-{slugify(title)}.md"
        return PageResolution(
            target_type="meeting",
            target_title=title,
            target_path=str(path),
            confidence=0.85,
            reason="matched meeting keyword",
        )

    company = next((name for name in COMPANY_NAMES if name in text), "")
    if company and any(keyword in text for keyword in PROJECT_KEYWORDS):
        title = f"{company.title()} Project"
        return _project(vault, title, 0.7, "matched company plus project keyword")

    date = item.captured_at[:10] if item.captured_at else "undated"
    slug = slugify(item.title)
    path = vault / "00-inbox" / f"{date}-{slug}.md"
    return PageResolution(
        target_type="inbox",
        target_title=item.title,
        target_path=str(path),
        confidence=0.35,
        reason="low confidence; routed to inbox for review",
    )


def _project(vault: Path, title: str, confidence: float, reason: str) -> PageResolution:
    path = vault / "03-projects" / f"{slugify(title)}.md"
    return PageResolution("project", title, str(path), confidence, reason)


def _learned_route(item: IngestInput, vault: Path) -> PageResolution | None:
    records = load_memory_records(str(vault))
    embeddings = load_memory_embeddings(str(vault))
    if not records or not embeddings:
        return None

    current_embedding = build_embedding(f"{item.title}\n\n{item.content}")
    best_match: tuple[float, dict] | None = None
    item_text = f"{item.title}\n{item.content}".lower()

    for record in records:
        content_hash = record.get("content_hash")
        if not isinstance(content_hash, str) or content_hash not in embeddings:
            continue
        routing = record.get("routing") or {}
        target_type = routing.get("target_type")
        target_title = routing.get("target_title")
        target_path = routing.get("target_path")
        if not all(isinstance(value, str) and value for value in [target_type, target_title, target_path]):
            continue
        if target_type == "inbox":
            continue

        record_source = record.get("source") or {}
        record_text = f"{record_source.get('title', '')}\n{record.get('processing', {}).get('summary', '')}".lower()
        lexical_bonus = 0.0
        if record_text:
            shared_tokens = {
                token for token in item_text.split()
                if len(token) > 2 and token in record_text
            }
            lexical_bonus = min(len(shared_tokens) * 0.03, 0.15)

        similarity = _cosine_similarity(current_embedding, embeddings[content_hash]) + lexical_bonus
        if similarity < 0.82:
            continue
        if best_match is None or similarity > best_match[0]:
            best_match = (similarity, record)

    if best_match is None:
        return None

    similarity, record = best_match
    routing = record["routing"]
    return PageResolution(
        target_type=routing["target_type"],
        target_title=routing["target_title"],
        target_path=routing["target_path"],
        confidence=min(similarity, 0.97),
        reason=f"matched similar stored memory item ({record.get('content_hash', 'unknown')[:8]})",
    )


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or not left:
        return 0.0
    return sum(a * b for a, b in zip(left, right))
