from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .router import slugify
from .schema import IngestInput


CLIENTS = ["Woolworths", "Coles", "Bunnings", "Dan Murphy's", "Internal"]
SOLUTIONS = [
    "Smart Trolley",
    "ESL",
    "AI Camera",
    "RMN",
    "Contract",
    "Technical Architecture",
    "Commercial",
    "Support",
]


@dataclass(frozen=True)
class ReviewDecision:
    status: str
    review_status: str
    top_category: str
    client: str
    project: str
    solution: str
    document_type: str
    topic: str
    sensitivity: str
    confidence: float
    suggested_folder: str
    final_folder: str
    output_path: str
    auto_commit_allowed: bool
    reasons: list[str] = field(default_factory=list)


def decide_review(
    item: IngestInput,
    processed,
    resolution,
    vault_path: str,
    *,
    auto_commit_enabled: bool = False,
) -> ReviewDecision:
    text = f"{item.title}\n{item.content}".lower()
    client = detect_client(text)
    solution = detect_solution(text)
    document_type = detect_document_type(text, processed.classification.note_type)
    sensitivity = detect_sensitivity(text, client)
    confidence = round(min(float(processed.classification.confidence), float(resolution.confidence)), 3)
    final_folder = str(Path(resolution.target_path).parent)
    suggested_folder = final_folder
    project = resolution.target_title if resolution.target_type == "project" else ""
    reasons: list[str] = []

    if processed.duplicate_of:
        reasons.append("possible duplicate")
    if confidence < 0.85:
        reasons.append("confidence below 0.85")
    if sensitivity in {"commercial_sensitive", "legal_review_required"}:
        reasons.append(f"sensitivity requires review: {sensitivity}")
    if not client and _looks_work_related(text):
        reasons.append("unknown work client")
    if resolution.target_type == "inbox":
        reasons.append("resolver selected inbox/review destination")

    auto_commit_allowed = (
        auto_commit_enabled
        and confidence >= 0.85
        and sensitivity not in {"commercial_sensitive", "legal_review_required"}
        and not processed.duplicate_of
        and not (not client and _looks_work_related(text))
        and resolution.target_type != "inbox"
    )

    if auto_commit_allowed:
        status = "committed"
        review_status = "passed"
        output_path = resolution.target_path
    else:
        status = "staged"
        review_status = "pending"
        date = item.captured_at[:10] if item.captured_at else "undated"
        output_path = str(Path(vault_path) / "00_Inbox" / "Gbrain_Review" / f"{date}-{slugify(item.title)}.md")
        if not reasons:
            reasons.append("auto-commit disabled")

    return ReviewDecision(
        status=status,
        review_status=review_status,
        top_category=detect_top_category(text),
        client=client,
        project=project,
        solution=solution,
        document_type=document_type,
        topic=item.title,
        sensitivity=sensitivity,
        confidence=confidence,
        suggested_folder=suggested_folder,
        final_folder=final_folder if auto_commit_allowed else "",
        output_path=output_path,
        auto_commit_allowed=auto_commit_allowed,
        reasons=reasons,
    )


def frontmatter_for_decision(decision: ReviewDecision, source: str = "gbrain") -> dict[str, object]:
    return {
        "source": source,
        "status": decision.status,
        "review_status": decision.review_status,
        "top_category": decision.top_category,
        "client": decision.client,
        "project": decision.project,
        "solution": decision.solution,
        "topic": decision.topic,
        "type": decision.document_type,
        "sensitivity": decision.sensitivity,
        "confidence": decision.confidence,
        "suggested_folder": decision.suggested_folder,
        "final_folder": decision.final_folder,
    }


def detect_top_category(text: str) -> str:
    if _looks_work_related(text):
        return "Work"
    if any(word in text for word in ["invoice", "tax", "bank", "payment", "finance"]):
        return "Finance"
    if any(word in text for word in ["course", "learn", "research", "study"]):
        return "Learning"
    if any(word in text for word in ["home", "house", "apartment"]):
        return "Home"
    return "Personal"


def detect_client(text: str) -> str:
    if "dan murphy" in text or "dan murphy's" in text:
        return "Dan Murphy's"
    for client in CLIENTS:
        if client.lower() in text:
            return client
    if any(word in text for word in ["internal", "hanshow", "riti tec"]):
        return "Internal"
    return ""


def detect_solution(text: str) -> str:
    checks = {
        "Smart Trolley": ["smart trolley", "smart cart", "trolley", "cart"],
        "ESL": ["esl", "electronic shelf label"],
        "AI Camera": ["ai camera", "camera"],
        "RMN": ["rmn", "retail media"],
        "Contract": ["contract", "clause", "legal"],
        "Technical Architecture": ["architecture", "integration", "api", "technical"],
        "Commercial": ["price", "pricing", "cost", "budget", "quote", "commercial"],
        "Support": ["support", "issue", "bug", "incident"],
    }
    for solution, keywords in checks.items():
        if any(keyword in text for keyword in keywords):
            return solution
    return "Other"


def detect_document_type(text: str, note_type: str) -> str:
    if note_type == "meeting":
        return "Meeting Notes"
    if note_type == "decision":
        return "Action Item"
    if any(word in text for word in ["meeting", "minutes", "workshop", "call", "会议", "纪要"]):
        return "Meeting Notes"
    if any(word in text for word in ["email", "draft", "reply"]):
        return "Email Draft"
    if any(word in text for word in ["issue", "bug", "error", "failure"]):
        return "Technical Issue"
    if any(word in text for word in ["price", "budget", "quote", "commercial"]):
        return "Commercial Discussion"
    if any(word in text for word in ["contract", "clause", "msa", "terms"]):
        return "Contract Clause"
    if any(word in text for word in ["feedback", "customer says", "customer wants"]):
        return "Customer Feedback"
    if any(word in text for word in ["requirement", "must", "need to"]):
        return "Product Requirement"
    if any(word in text for word in ["todo", "action", "next step", "follow up"]):
        return "Action Item"
    if note_type == "document":
        return "Research"
    if note_type == "skill":
        return "Template"
    return "Other"


def detect_sensitivity(text: str, client: str) -> str:
    if any(word in text for word in ["legal review", "lawyer", "indemnity", "liability", "termination"]):
        return "legal_review_required"
    if any(word in text for word in ["price", "pricing", "cost", "budget", "margin", "discount", "quote", "po ", "purchase order"]):
        return "commercial_sensitive"
    if client and client != "Internal":
        return "customer_confidential"
    if any(word in text for word in ["internal", "confidential", "private"]):
        return "internal"
    return "internal"


def _looks_work_related(text: str) -> bool:
    work_words = [
        "customer",
        "client",
        "project",
        "pilot",
        "deployment",
        "contract",
        "commercial",
        "meeting",
        "woolworths",
        "coles",
        "bunnings",
        "dan murphy",
        "hanshow",
    ]
    return any(word in text for word in work_words)
