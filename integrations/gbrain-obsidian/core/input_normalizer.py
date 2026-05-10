import hashlib
import re
from typing import Iterable, List, Optional

from adapters.audio_file import AudioFileAdapter
from adapters.base import BaseInputAdapter
from adapters.email_message import EmailMessageAdapter
from adapters.file_document import FileDocumentAdapter
from adapters.image_file import ImageFileAdapter
from adapters.local_web import LocalWebAdapter
from adapters.telegram_text import TelegramTextAdapter
from adapters.video_file import VideoFileAdapter
from adapters.wechat_text import WeChatTextAdapter
from adapters.wechat_voice import WeChatVoiceAdapter
from core.schemas import HermesMessage, RawInputEvent
from tools.document_parser import parse_document
from tools.file_cleanup import delete_file_if_exists
from tools.ocr_tool import extract_text_from_image
from tools.stt_tool import transcribe_audio

COMMANDS = {"search", "save", "review", "approve", "reject", "status"}
COMMAND_RE = re.compile(r"^/([A-Za-z][\w-]*)(?:@\w+)?(?:\s+(.*))?$", re.DOTALL)


class UnknownInputSourceError(ValueError):
    pass


class InputNormalizer:
    def __init__(self, adapters: Optional[Iterable[BaseInputAdapter]] = None) -> None:
        self.adapters: List[BaseInputAdapter] = list(adapters or default_adapters())

    def to_raw_event(self, payload: dict) -> RawInputEvent:
        for adapter in self.adapters:
            if adapter.can_handle(payload):
                return adapter.to_raw_event(payload)
        raise UnknownInputSourceError("No input adapter could handle payload")

    def normalize_payload(self, payload: dict) -> HermesMessage:
        return self.normalize(self.to_raw_event(payload))

    def normalize(self, raw_event: RawInputEvent) -> HermesMessage:
        text = raw_event.content or ""
        flags = dict(raw_event.processing_flags)

        if raw_event.input_type == "audio":
            text = transcribe_audio(raw_event.file_path or "", raw_event.mime_type)
            flags["stt_completed"] = True
            if flags.get("delete_original_after_processing"):
                flags["original_deleted"] = delete_file_if_exists(raw_event.file_path)
            else:
                flags["original_deleted"] = False
        elif raw_event.input_type == "image":
            text = extract_text_from_image(raw_event.file_path or "", raw_event.mime_type)
            flags["ocr_completed"] = True
        elif raw_event.input_type == "document":
            text = parse_document(raw_event.file_path or "", raw_event.mime_type)
            flags["document_parse_completed"] = True
        elif raw_event.input_type == "video":
            flags["video_parse_pending"] = True
        elif raw_event.input_type == "mixed":
            flags["mixed_input_received"] = True

        command, command_args = extract_command(text)
        clean_text = command_args if command else text

        return HermesMessage(
            message_id=stable_message_id(raw_event, clean_text),
            source=raw_event.source,
            source_type=raw_event.source_type,
            input_type=raw_event.input_type,
            user_id=raw_event.user_id,
            timestamp=raw_event.timestamp,
            text=clean_text.strip(),
            language=detect_language(clean_text),
            command=command,
            command_args=command_args,
            mime_type=raw_event.mime_type,
            attachments=list(raw_event.attachments),
            metadata=dict(raw_event.metadata),
            processing_flags=flags,
        )


def default_adapters() -> List[BaseInputAdapter]:
    return [
        TelegramTextAdapter(),
        WeChatTextAdapter(),
        EmailMessageAdapter(),
        WeChatVoiceAdapter(),
        LocalWebAdapter(),
        FileDocumentAdapter(),
        AudioFileAdapter(),
        ImageFileAdapter(),
        VideoFileAdapter(),
    ]


def extract_command(text: str) -> tuple[str | None, str]:
    match = COMMAND_RE.match((text or "").strip())
    if not match:
        return None, ""
    command = match.group(1).lower()
    if command not in COMMANDS:
        return None, ""
    return command, (match.group(2) or "").strip()


def detect_language(text: str) -> str:
    for char in text or "":
        if "\u4e00" <= char <= "\u9fff":
            return "zh"
    return "en"


def stable_message_id(raw_event: RawInputEvent, text: str) -> str:
    seed = "|".join(
        [
            raw_event.source,
            raw_event.source_type,
            raw_event.user_id,
            raw_event.timestamp,
            raw_event.mime_type or "",
            raw_event.file_path or "",
            text.strip(),
        ]
    )
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:32]
