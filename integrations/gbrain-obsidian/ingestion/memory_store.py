from __future__ import annotations

import json
from difflib import SequenceMatcher
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .gbrain_processing import GBrainProcessingResult
from .schema import IngestInput


def memory_root(vault_path: str) -> Path:
    return Path(vault_path).expanduser().resolve().parent / "memory-store"


def existing_hashes(vault_path: str) -> set[str]:
    records = memory_root(vault_path) / "jsonl" / "records.jsonl"
    hashes: set[str] = set()
    if not records.exists():
        return hashes
    for line in records.read_text(encoding="utf-8").splitlines():
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        content_hash = payload.get("content_hash")
        if isinstance(content_hash, str):
            hashes.add(content_hash)
    return hashes


def load_memory_records(vault_path: str) -> list[dict[str, Any]]:
    records = memory_root(vault_path) / "jsonl" / "records.jsonl"
    loaded: list[dict[str, Any]] = []
    if not records.exists():
        return loaded
    for line in records.read_text(encoding="utf-8").splitlines():
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            loaded.append(payload)
    return loaded


def load_memory_embeddings(vault_path: str) -> dict[str, list[float]]:
    vectors = memory_root(vault_path) / "vector" / "embeddings.jsonl"
    loaded: dict[str, list[float]] = {}
    if not vectors.exists():
        return loaded
    for line in vectors.read_text(encoding="utf-8").splitlines():
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        content_hash = payload.get("content_hash")
        embedding = payload.get("embedding")
        if isinstance(content_hash, str) and isinstance(embedding, list):
            loaded[content_hash] = [float(value) for value in embedding]
    return loaded


def find_possible_duplicate(item: IngestInput, vault_path: str, content_hash: str) -> str | None:
    current_title = _normalized_title(item.title)
    for record in load_memory_records(vault_path):
        existing_hash = record.get("content_hash")
        if existing_hash == content_hash:
            return content_hash
        source = record.get("source") or {}
        existing_title = _normalized_title(str(source.get("title") or ""))
        if not current_title or not existing_title:
            continue
        if current_title == existing_title:
            return str(existing_hash or existing_title)
        if SequenceMatcher(None, current_title, existing_title).ratio() >= 0.92:
            return str(existing_hash or existing_title)
    return None


def write_memory_store(
    item: IngestInput,
    processed: GBrainProcessingResult,
    vault_path: str,
    resolution=None,
    decision=None,
) -> dict[str, str]:
    root = memory_root(vault_path)
    jsonl_dir = root / "jsonl"
    vector_dir = root / "vector"
    graph_dir = root / "graph"
    for path in (jsonl_dir, vector_dir, graph_dir):
        path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    record = {
        "stored_at": timestamp,
        "content_hash": processed.content_hash,
        "duplicate_of": processed.duplicate_of,
        "source": {
            "source_type": item.source_type,
            "source_app": item.source_app,
            "captured_at": item.captured_at,
            "title": item.title,
            "attachments": item.attachments,
            "metadata": item.metadata,
        },
        "processing": {
            "note_type": processed.classification.note_type,
            "classification_confidence": processed.classification.confidence,
            "classification_reason": processed.classification.reason,
            "score": processed.score,
            "summary": processed.summary,
            "entities": processed.entities,
            "action_items": processed.action_items,
            "relations": processed.relations,
            "tags": processed.tags,
            "sensitivity": getattr(decision, "sensitivity", None),
        },
        "routing": {
            "target_type": getattr(resolution, "target_type", None),
            "target_title": getattr(resolution, "target_title", None),
            "target_path": getattr(resolution, "target_path", None),
            "confidence": getattr(resolution, "confidence", None),
            "reason": getattr(resolution, "reason", None),
            "suggested_folder": getattr(decision, "suggested_folder", None),
            "final_folder": getattr(decision, "final_folder", None),
            "output_path": getattr(decision, "output_path", None),
        },
        "workflow": {
            "status": getattr(decision, "status", None),
            "review_status": getattr(decision, "review_status", None),
            "auto_commit_allowed": getattr(decision, "auto_commit_allowed", None),
            "review_reasons": getattr(decision, "reasons", []),
        },
    }
    vector_record = {
        "content_hash": processed.content_hash,
        "embedding_model": "local-deterministic-smoke",
        "embedding": processed.embedding,
    }
    graph_record = {
        "content_hash": processed.content_hash,
        "entities": processed.entities,
        "relations": processed.relations,
    }

    records_path = jsonl_dir / "records.jsonl"
    vectors_path = vector_dir / "embeddings.jsonl"
    graph_path = graph_dir / "relations.jsonl"
    records_path.open("a", encoding="utf-8").write(json.dumps(record, ensure_ascii=False) + "\n")
    if processed.duplicate_of is None:
        vectors_path.open("a", encoding="utf-8").write(json.dumps(vector_record, ensure_ascii=False) + "\n")
        graph_path.open("a", encoding="utf-8").write(json.dumps(graph_record, ensure_ascii=False) + "\n")

    return {
        "jsonl": str(records_path),
        "vector": str(vectors_path),
        "graph": str(graph_path),
    }


def write_processing_log(
    item: IngestInput,
    processed: GBrainProcessingResult,
    vault_path: str,
    resolution=None,
    decision=None,
) -> str:
    jsonl_dir = memory_root(vault_path) / "jsonl"
    jsonl_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    path = jsonl_dir / "processing-log.jsonl"
    record = {
        "timestamp": timestamp,
        "source_path": item.metadata.get("source_path") or item.metadata.get("file_path") or "",
        "content_hash": processed.content_hash,
        "duplicate_of": processed.duplicate_of,
        "status": getattr(decision, "status", "classified"),
        "review_status": getattr(decision, "review_status", "pending"),
        "classification": {
            "note_type": processed.classification.note_type,
            "confidence": processed.classification.confidence,
            "reason": processed.classification.reason,
        },
        "routing": {
            "suggested_target_folder": getattr(decision, "suggested_folder", None),
            "final_path": getattr(decision, "output_path", None),
            "resolver_target_path": getattr(resolution, "target_path", None),
            "resolver_confidence": getattr(resolution, "confidence", None),
        },
        "review": {
            "result": getattr(decision, "review_status", "pending"),
            "reasons": getattr(decision, "reasons", []),
        },
        "sensitivity": getattr(decision, "sensitivity", None),
        "action_items": processed.action_items,
    }
    path.open("a", encoding="utf-8").write(json.dumps(record, ensure_ascii=False) + "\n")
    return str(path)


def _normalized_title(title: str) -> str:
    return " ".join(title.lower().strip().split())
