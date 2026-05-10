import json
import os
from pathlib import Path

from ingestion.pipeline import ingest
from ingestion.schema import IngestInput


def test_pipeline_voice_writes_woolworths_n70_project(tmp_path, monkeypatch):
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(tmp_path / "obsidian-vault"))
    monkeypatch.setenv("MIN_STORE_SCORE", "3")
    monkeypatch.setenv("SAVE_RAW_CONTENT", "false")
    monkeypatch.setenv("GBRAIN_ENABLED", "false")
    payload = json.loads(Path("connectors/voice/example_wechat_woolworths_n70.json").read_text(encoding="utf-8"))

    result = ingest(IngestInput.from_payload(payload))

    page = tmp_path / "obsidian-vault/00_Inbox/Gbrain_Review/2026-04-25-woolworths-n70-robot-test-unit-follow-up.md"
    assert result.should_store is True
    assert result.status == "staged"
    assert result.review_status == "pending"
    assert result.sensitivity == "customer_confidential"
    assert page.exists()
    text = page.read_text(encoding="utf-8")
    assert 'source: "gbrain"' in text
    assert 'status: "staged"' in text
    assert 'review_status: "pending"' in text
    assert 'client: "Woolworths"' in text
    assert 'suggested_folder:' in text
    assert "## Compiled Truth" in text
    assert "## AI Summary" in text
    assert "## Action Items" in text
    assert "## Timeline" in text
    assert "2026-04-25" in text
    assert "Woolworths" in text
    assert "N70" in text
    assert "2026-04-25-wechat-woolworths-n70.m4a" in text
    assert "## Raw Content" not in text
    assert result.processing_log_path


def test_pipeline_dry_run_does_not_write_files(tmp_path, monkeypatch):
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(tmp_path / "obsidian-vault"))
    monkeypatch.setenv("MIN_STORE_SCORE", "3")
    monkeypatch.setenv("SAVE_RAW_CONTENT", "false")
    monkeypatch.setenv("GBRAIN_ENABLED", "false")
    monkeypatch.setenv("GBRAIN_DRY_RUN", "true")
    payload = json.loads(Path("connectors/voice/example_wechat_woolworths_n70.json").read_text(encoding="utf-8"))

    result = ingest(IngestInput.from_payload(payload))

    assert result.should_store is True
    assert result.dry_run is True
    assert result.output_path
    assert not Path(result.output_path).exists()
    assert not (tmp_path / "memory-store/jsonl/records.jsonl").exists()
