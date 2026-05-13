from ingestion.page_resolver import resolve_page
from ingestion.schema import IngestInput
from ingestion.gbrain_processing import process_with_gbrain
from ingestion.memory_store import write_memory_store


def test_n70_woolworths_resolves_to_project_page(tmp_path):
    item = IngestInput(
        source_type="voice",
        source_app="wechat",
        captured_at="2026-04-25T14:30:00+10:00",
        title="Woolworths N70 robot test unit follow-up",
        content="Woolworths wants the N70 large robot test unit.",
        attachments=[],
    )

    resolution = resolve_page(item, str(tmp_path))

    assert resolution.target_type == "project"
    assert resolution.target_title == "Woolworths N70 Robot Test Unit"
    assert resolution.target_path.endswith("03-projects/woolworths-n70-robot-test-unit.md")


def test_learned_route_prefers_similar_memory_record(tmp_path):
    vault = tmp_path / "obsidian-vault"
    vault.mkdir()
    seed = IngestInput(
        source_type="text",
        source_app="wechat",
        captured_at="2026-05-10T10:00:00+10:00",
        title="Hanshow Australia rollout project",
        content="Hanshow customer rollout project needs deployment planning and pilot timeline.",
        attachments=[],
    )
    seed_resolution = resolve_page(seed, str(vault))
    processed = process_with_gbrain(seed, existing_hashes=set())
    write_memory_store(seed, processed, str(vault), resolution=seed_resolution)

    similar = IngestInput(
        source_type="text",
        source_app="wechat",
        captured_at="2026-05-10T10:05:00+10:00",
        title="Hanshow deployment planning update",
        content="Customer rollout timeline, deployment work, and pilot planning for Hanshow Australia.",
        attachments=[],
    )

    resolution = resolve_page(similar, str(vault))

    assert resolution.target_type == "project"
    assert resolution.target_path.endswith("03-projects/hanshow-project.md")
    assert "similar stored memory item" in resolution.reason
