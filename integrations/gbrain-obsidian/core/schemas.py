from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

InputType = Literal["text", "audio", "image", "document", "video", "mixed"]


@dataclass
class RawInputEvent:
    source: str
    source_type: str
    input_type: InputType
    user_id: str
    timestamp: str
    content: Optional[str] = None
    file_path: Optional[str] = None
    mime_type: Optional[str] = None
    attachments: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    processing_flags: Dict[str, bool] = field(default_factory=dict)


@dataclass
class HermesMessage:
    message_id: str
    source: str
    source_type: str
    input_type: InputType
    user_id: str
    timestamp: str
    text: str
    language: Literal["en", "zh"]
    command: Optional[str] = None
    command_args: str = ""
    mime_type: Optional[str] = None
    attachments: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    processing_flags: Dict[str, bool] = field(default_factory=dict)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
