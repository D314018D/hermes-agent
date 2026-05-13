from typing import Any, Dict

from adapters.base import BaseInputAdapter
from core.schemas import RawInputEvent, utc_now_iso


class WeChatTextAdapter(BaseInputAdapter):
    source = "wechat"
    source_type = "wechat_text"

    def can_handle(self, payload: Dict[str, Any]) -> bool:
        source_match = payload.get("source") == self.source or payload.get("platform") == self.source
        type_match = payload.get("source_type") in {self.source_type, "text", "wechat_text"}
        has_text = bool(payload.get("text") or payload.get("content") or payload.get("message"))
        return (source_match or type_match) and has_text

    def to_raw_event(self, payload: Dict[str, Any]) -> RawInputEvent:
        text = str(payload.get("text") or payload.get("content") or payload.get("message") or "")
        return RawInputEvent(
            source=self.source,
            source_type=self.source_type,
            input_type="text",
            user_id=str(payload.get("user_id") or payload.get("from_user") or payload.get("chat_id") or "unknown"),
            timestamp=str(payload.get("timestamp") or payload.get("captured_at") or utc_now_iso()),
            content=text,
            attachments=[str(item) for item in (payload.get("attachments") or [])],
            metadata={
                "chat_id": str(payload.get("chat_id") or ""),
                "message_platform_id": str(payload.get("message_id") or ""),
                "session_id": str(payload.get("session_id") or ""),
            },
            processing_flags={
                "raw_content_logged": False,
            },
        )
