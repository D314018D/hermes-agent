from pathlib import Path

import pytest

from core.input_normalizer import InputNormalizer, UnknownInputSourceError


def test_telegram_text_command_normalization():
    message = InputNormalizer().normalize_payload(
        {
            "source": "telegram",
            "text": "/search Woolworths N70",
            "user_id": "richard",
            "chat_id": "chat-1",
            "message_id": "msg-1",
            "timestamp": "2026-04-25T14:00:00+10:00",
        }
    )

    assert message.command == "search"
    assert message.command_args == "Woolworths N70"
    assert message.text == "Woolworths N70"
    assert message.language == "en"
    assert message.source_type == "telegram_text"
    assert len(message.message_id) == 32
    assert message.processing_flags["raw_content_logged"] is False


def test_wechat_voice_normalization_retains_audio_by_default(tmp_path, monkeypatch):
    audio = tmp_path / "voice.m4a"
    audio.write_bytes(b"fake audio")

    def fake_transcribe(file_path, mime_type=None):
        assert file_path == str(audio)
        assert mime_type == "audio/mp4"
        return "批准 N70 样机"

    monkeypatch.setattr("core.input_normalizer.transcribe_audio", fake_transcribe)

    message = InputNormalizer().normalize_payload(
        {
            "source": "wechat",
            "source_type": "wechat_voice",
            "file_path": str(audio),
            "mime_type": "audio/mp4",
            "user_id": "richard",
            "timestamp": "2026-04-25T15:30:00+10:00",
        }
    )

    assert message.text == "批准 N70 样机"
    assert message.language == "zh"
    assert message.processing_flags["stt_completed"] is True
    assert message.processing_flags["original_deleted"] is False
    assert audio.exists()


def test_wechat_voice_can_delete_audio_after_success_with_explicit_opt_in(tmp_path, monkeypatch):
    audio = tmp_path / "voice.m4a"
    audio.write_bytes(b"fake audio")

    monkeypatch.setattr("core.input_normalizer.transcribe_audio", lambda file_path, mime_type=None: "批准 N70 样机")

    message = InputNormalizer().normalize_payload(
        {
            "source": "wechat",
            "source_type": "wechat_voice",
            "file_path": str(audio),
            "user_id": "richard",
            "delete_original_after_processing": True,
        }
    )

    assert message.processing_flags["original_deleted"] is True
    assert not audio.exists()


def test_wechat_voice_retains_audio_if_stt_fails(tmp_path, monkeypatch):
    audio = tmp_path / "voice.m4a"
    audio.write_bytes(b"fake audio")

    def broken_transcribe(file_path, mime_type=None):
        raise RuntimeError("stt failed")

    monkeypatch.setattr("core.input_normalizer.transcribe_audio", broken_transcribe)

    with pytest.raises(RuntimeError):
        InputNormalizer().normalize_payload(
            {
                "source": "wechat",
                "source_type": "wechat_voice",
                "file_path": str(audio),
                "user_id": "richard",
            }
        )

    assert audio.exists()


def test_local_web_text_normalization():
    message = InputNormalizer().normalize_payload(
        {
            "source": "local_web",
            "content": "Check router status",
            "session_id": "browser-session",
            "timestamp": "2026-04-25T16:00:00+10:00",
        }
    )

    assert message.source == "local_web"
    assert message.source_type == "local_web_text"
    assert message.user_id == "browser-session"
    assert message.text == "Check router status"
    assert message.command is None


def test_unknown_input_source_handling():
    with pytest.raises(UnknownInputSourceError):
        InputNormalizer().normalize_payload({"source": "carrier_pigeon", "content": "hello"})


def test_future_document_adapter_placeholder(monkeypatch):
    monkeypatch.setattr("core.input_normalizer.parse_document", lambda file_path, mime_type=None: "Parsed document")

    message = InputNormalizer().normalize_payload(
        {
            "source_type": "file_document",
            "file_path": "/tmp/example.pdf",
            "mime_type": "application/pdf",
            "user_id": "richard",
            "timestamp": "2026-04-25T17:00:00+10:00",
        }
    )

    assert message.input_type == "document"
    assert message.text == "Parsed document"
    assert message.processing_flags["requires_document_parse"] is True
    assert message.processing_flags["document_parse_completed"] is True
