from typing import Any, Dict

from adapters.base import BaseInputAdapter
from core.schemas import RawInputEvent, utc_now_iso


class EmailMessageAdapter(BaseInputAdapter):
    source = "email"
    source_type = "email_message"

    def can_handle(self, payload: Dict[str, Any]) -> bool:
        source_match = payload.get("source") == self.source or payload.get("platform") == self.source
        type_match = payload.get("source_type") in {self.source_type, "email"}
        has_body = bool(payload.get("body") or payload.get("content") or payload.get("text"))
        return (source_match or type_match) and has_body

    def to_raw_event(self, payload: Dict[str, Any]) -> RawInputEvent:
        subject = str(payload.get("subject") or "").strip()
        body = str(payload.get("body") or payload.get("content") or payload.get("text") or "")
        content = f"{subject}\n\n{body}".strip() if subject else body
        return RawInputEvent(
            source=self.source,
            source_type=self.source_type,
            input_type="text",
            user_id=str(payload.get("from") or payload.get("sender") or payload.get("user_id") or "unknown"),
            timestamp=str(payload.get("timestamp") or payload.get("captured_at") or utc_now_iso()),
            content=content,
            attachments=[str(item) for item in (payload.get("attachments") or [])],
            mime_type="text/plain",
            metadata={
                "from": str(payload.get("from") or payload.get("sender") or ""),
                "to": str(payload.get("to") or ""),
                "subject": subject,
                "message_platform_id": str(payload.get("message_id") or ""),
            },
            processing_flags={"raw_content_logged": False},
        )
