import os
from .schema import IngestInput, IngestResult
from .renderer import render_markdown
from .page_resolver import PageResolution, resolve_page
from .brain_page_writer import write_brain_page
from .gbrain_processing import process_with_gbrain
from .memory_store import existing_hashes, find_possible_duplicate, write_memory_store, write_processing_log
from .review_policy import decide_review, frontmatter_for_decision


def try_gbrain_sync(vault: str) -> None:
    if os.getenv("GBRAIN_ENABLED", "false").lower() != "true":
        return
    try:
        from maintenance.gbrain_sync import sync

        sync(vault)
    except Exception:
        # GBrain is optional for core local-first ingestion.
        return


def hermes_vault_writes_disabled(item: IngestInput) -> bool:
    mode = os.getenv("HERMES_OBSIDIAN_WRITE_MODE", "read_only").strip().lower()
    if mode not in {"read_only", "readonly"}:
        return False

    source_app = item.source_app.strip().lower()
    if source_app == "hermes_plugin" or source_app.endswith("_agent"):
        return True
    return item.metadata.get("writer", "").strip().lower() == "hermes"


def ingest(item: IngestInput) -> IngestResult:
    min_score = int(os.getenv("MIN_STORE_SCORE", "3"))
    vault = os.getenv("OBSIDIAN_VAULT_PATH", "./obsidian-vault")
    save_raw = os.getenv("SAVE_RAW_CONTENT", "false").lower() == "true"
    store_low = os.getenv("STORE_LOW_VALUE_TO_INBOX", "false").lower() == "true"
    dry_run = os.getenv("GBRAIN_DRY_RUN", "false").lower() == "true"
    auto_commit = os.getenv("GBRAIN_AUTO_COMMIT", "false").lower() == "true"

    processed = process_with_gbrain(item, existing_hashes(vault))
    possible_duplicate = find_possible_duplicate(item, vault, processed.content_hash)
    if possible_duplicate:
        processed.duplicate_of = possible_duplicate
    score = processed.score
    classification = processed.classification
    note_type = classification.note_type
    should_store = score >= min_score or note_type in ["meeting", "decision", "project", "document", "skill"]
    if not should_store and store_low:
        should_store = True

    markdown, summary, entities, tags = render_markdown(
        item,
        note_type,
        score,
        save_raw,
        summary=processed.summary,
        entities=processed.entities,
        tags=processed.tags,
        relations=processed.relations,
    )
    output_path = None
    memory_paths = {}
    processing_log_path = None
    decision = None

    if should_store:
        if hermes_vault_writes_disabled(item):
            return IngestResult(
                should_store=False,
                score=score,
                note_type=note_type,
                classification_confidence=classification.confidence,
                classification_reason=classification.reason,
                status="blocked",
                review_status="read_only",
                sensitivity="",
                confidence=classification.confidence,
                suggested_folder="",
                final_folder="",
                title=item.title,
                summary=summary,
                entities=entities,
                action_items=processed.action_items,
                tags=tags + ["hermes_read_only"],
                markdown=markdown,
                relations=processed.relations,
                duplicate_of=processed.duplicate_of,
                dry_run=True,
            )
        resolution = resolve_page(item, vault)
        decision = decide_review(item, processed, resolution, vault, auto_commit_enabled=auto_commit)
        if decision.review_status == "pending":
            tags = tags + ["needs_review", decision.status]
        else:
            tags = tags + [decision.status]
        output_resolution = resolution
        if not decision.auto_commit_allowed:
            output_resolution = PageResolution(
                target_type="inbox",
                target_title=resolution.target_title,
                target_path=decision.output_path,
                confidence=decision.confidence,
                reason="held for Gbrain review: " + "; ".join(decision.reasons),
            )
        output_path = write_brain_page(
            item,
            output_resolution,
            summary,
            entities,
            tags,
            processed.relations,
            action_items=processed.action_items,
            frontmatter=frontmatter_for_decision(decision),
            dry_run=dry_run,
        )
        if not dry_run:
            memory_paths = write_memory_store(item, processed, vault, resolution=resolution, decision=decision)
            processing_log_path = write_processing_log(item, processed, vault, resolution=resolution, decision=decision)
            try_gbrain_sync(vault)

    return IngestResult(
        should_store=should_store,
        score=score,
        note_type=note_type,
        classification_confidence=classification.confidence,
        classification_reason=classification.reason,
        status=getattr(decision, "status", "captured"),
        review_status=getattr(decision, "review_status", "not_stored"),
        sensitivity=getattr(decision, "sensitivity", ""),
        confidence=getattr(decision, "confidence", classification.confidence),
        suggested_folder=getattr(decision, "suggested_folder", ""),
        final_folder=getattr(decision, "final_folder", ""),
        title=item.title,
        summary=summary,
        entities=entities,
        action_items=processed.action_items,
        tags=tags,
        markdown=markdown,
        output_path=output_path,
        relations=processed.relations,
        memory_paths=memory_paths,
        processing_log_path=processing_log_path,
        duplicate_of=processed.duplicate_of,
        dry_run=dry_run,
    )
