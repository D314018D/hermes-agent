from dataclasses import dataclass
from .schema import IngestInput, NoteType

@dataclass(frozen=True)
class Classification:
    note_type: NoteType
    confidence: float
    reason: str

def classify_input(item: IngestInput) -> Classification:
    text = f"{item.title}\n{item.content}".lower()

    if any(k in text for k in ["model", "chatgpt", "chatgtp", "qwen", "hermes", "router", "routing", "模型", "路由"]):
        return Classification("skill", 0.85, "model routing/configuration keyword match")

    if item.source_type == "file":
        return Classification("document", 0.9, "file sources are routed as documents")

    if item.source_type == "email":
        subject = item.metadata.get("subject", item.title).lower()
        if any(k in subject for k in ["re:", "meeting", "follow-up", "follow up", "minutes"]):
            return Classification("meeting", 0.75, "email subject looks meeting-related")

    if any(k in text for k in [
        "meeting", "call", "workshop", "discussion", "follow-up", "follow up",
        "会议", "会谈", "纪要", "讨论", "跟进", "截图",
    ]):
        return Classification("meeting", 0.85, "meeting keyword match")

    if any(k in text for k in ["decision", "approved", "confirmed", "agreed", "final decision"]):
        return Classification("decision", 0.85, "decision keyword match")

    if any(k in text for k in ["project", "poc", "pilot", "rollout", "deployment", "roadmap"]):
        return Classification("project", 0.8, "project keyword match")

    if any(k in text for k in ["company", "retailer", "customer", "client"]):
        return Classification("company", 0.7, "company keyword match")

    if any(k in text for k in ["contact", "person", "manager", "director", "ceo", "head of"]):
        return Classification("person", 0.7, "person keyword match")

    return Classification("inbox", 0.4, "no deterministic rule matched")
