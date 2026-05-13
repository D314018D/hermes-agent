from ingestion.schema import IngestInput
from ingestion.timeline_appender import append_timeline


def test_timeline_appender_preserves_existing_entries_and_appends_source():
    existing = """# Page

## Timeline

### 2026-04-24 — manual/text

Source: source_type=text

- Existing evidence

## References
"""
    item = IngestInput(
        source_type="voice",
        source_app="wechat",
        captured_at="2026-04-25T14:30:00+10:00",
        title="Follow-up",
        content="New evidence",
    )

    updated = append_timeline(existing, item, "source_type=voice; source_app=wechat", ["New evidence"])

    assert "Existing evidence" in updated
    assert "### 2026-04-25 — wechat/voice" in updated
    assert "Source: source_type=voice; source_app=wechat" in updated
    assert updated.index("Existing evidence") < updated.index("New evidence")

