from typing import Any, Dict

from adapters.base import BaseInputAdapter
from core.schemas import RawInputEvent, utc_now_iso


class TelegramTextAdapter(BaseInputAdapter):
    source = "telegram"
    source_type = "telegram_text"

    def can_handle(self, payload: Dict[str, Any]) -> bool:
        return (
            payload.get("source") == self.source
            or payload.get("platform") == self.source
            or payload.get("source_type") == self.source_type
        ) and bool(payload.get("text") or payload.get("content"))

    def to_raw_event(self, payload: Dict[str, Any]) -> RawInputEvent:
        return RawInputEvent(
            source=self.source,
            source_type=self.source_type,
            input_type="text",
            user_id=str(payload.get("user_id") or payload.get("chat_id") or "unknown"),
            timestamp=str(payload.get("timestamp") or payload.get("captured_at") or utc_now_iso()),
            content=str(payload.get("text") or payload.get("content") or ""),
            mime_type="text/plain",
            metadata={
                "chat_id": payload.get("chat_id"),
                "message_platform_id": payload.get("message_id"),
            },
            processing_flags={"raw_content_logged": False},
        )
