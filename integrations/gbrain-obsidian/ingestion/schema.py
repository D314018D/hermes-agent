from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

SourceType = Literal["text", "voice", "file", "email"]
NoteType = Literal["inbox", "person", "company", "project", "meeting", "decision", "document", "skill"]

@dataclass
class IngestInput:
    source_type: SourceType
    source_app: str
    captured_at: str
    title: str
    content: str
    attachments: List[str] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "IngestInput":
        source_type = payload.get("source_type", "text")
        if source_type not in ("text", "voice", "file", "email"):
            raise ValueError(f"Unsupported source_type: {source_type}")

        content = str(payload.get("content") or "").strip()
        metadata = {str(k): str(v) for k, v in (payload.get("metadata") or {}).items()}
        title = str(payload.get("title") or "").strip()
        if not title:
            title = metadata.get("subject") or default_title(content, source_type)

        captured_at = str(payload.get("captured_at") or "").strip()
        if not captured_at:
            captured_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

        attachments = payload.get("attachments") or []
        if not isinstance(attachments, list):
            raise ValueError("attachments must be a list")

        return cls(
            source_type=source_type,
            source_app=str(payload.get("source_app") or "unknown"),
            captured_at=captured_at,
            title=title,
            content=content,
            attachments=[str(item) for item in attachments],
            metadata=metadata,
        )


def default_title(content: str, source_type: SourceType) -> str:
    clean = " ".join(content.split())
    if clean:
        return clean[:72].rstrip(" .,;:") or f"Untitled {source_type}"
    return f"Untitled {source_type}"

@dataclass
class IngestResult:
    should_store: bool
    score: int
    note_type: NoteType
    classification_confidence: float
    classification_reason: str
    status: str
    review_status: str
    sensitivity: str
    confidence: float
    suggested_folder: str
    final_folder: str
    title: str
    summary: str
    entities: List[str]
    action_items: List[str]
    tags: List[str]
    markdown: str
    output_path: Optional[str] = None
    relations: List[Dict[str, str]] = field(default_factory=list)
    memory_paths: Dict[str, str] = field(default_factory=dict)
    processing_log_path: Optional[str] = None
    duplicate_of: Optional[str] = None
    dry_run: bool = False
