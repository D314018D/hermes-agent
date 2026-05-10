from typing import Any, Dict

from adapters.base import BaseInputAdapter
from core.schemas import RawInputEvent, utc_now_iso


class WeChatVoiceAdapter(BaseInputAdapter):
    source = "wechat"
    source_type = "wechat_voice"

    def can_handle(self, payload: Dict[str, Any]) -> bool:
        source_match = payload.get("source") == self.source or payload.get("platform") == self.source
        type_match = payload.get("source_type") in {self.source_type, "voice", "wechat_voice"}
        return (source_match or type_match) and bool(payload.get("file_path") or payload.get("audio_path"))

    def to_raw_event(self, payload: Dict[str, Any]) -> RawInputEvent:
        file_path = str(payload.get("file_path") or payload.get("audio_path") or "")
        return RawInputEvent(
            source=self.source,
            source_type=self.source_type,
            input_type="audio",
            user_id=str(payload.get("user_id") or payload.get("from_user") or "unknown"),
            timestamp=str(payload.get("timestamp") or payload.get("captured_at") or utc_now_iso()),
            file_path=file_path,
            mime_type=str(payload.get("mime_type") or "audio/mpeg"),
            metadata={"message_platform_id": payload.get("message_id")},
            processing_flags={
                "requires_stt": True,
                "delete_original_after_processing": bool(payload.get("delete_original_after_processing", False)),
                "raw_content_logged": False,
            },
        )
