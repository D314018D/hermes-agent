from typing import Any, Dict

from adapters.base import BaseInputAdapter
from core.schemas import RawInputEvent, utc_now_iso


class VideoFileAdapter(BaseInputAdapter):
    source = "video_file"
    source_type = "video_file"

    def can_handle(self, payload: Dict[str, Any]) -> bool:
        return payload.get("source_type") == self.source_type or payload.get("input_type") == "video"

    def to_raw_event(self, payload: Dict[str, Any]) -> RawInputEvent:
        return RawInputEvent(
            source=str(payload.get("source") or self.source),
            source_type=self.source_type,
            input_type="video",
            user_id=str(payload.get("user_id") or "unknown"),
            timestamp=str(payload.get("timestamp") or payload.get("captured_at") or utc_now_iso()),
            file_path=str(payload.get("file_path") or ""),
            mime_type=payload.get("mime_type"),
            metadata={"placeholder": True},
            processing_flags={"requires_video_parse": True, "raw_content_logged": False},
        )
