from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _project_root() -> Path:
    configured = os.environ.get("HERMES_OBSIDIAN_GBRAIN_ROOT", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return Path("/Users/rl_home/Documents/Codex/Hermes_Agent/integrations/gbrain-obsidian")


ROOT = _project_root()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
try:
    from env import load_local_env

    load_local_env()
except Exception:
    pass


def _json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False)


def _default_vault(vault_path: str | None = None) -> str:
    if vault_path:
        return str(Path(vault_path).expanduser())
    return os.environ.get("OBSIDIAN_VAULT_PATH") or str(ROOT / "obsidian-vault")


def gbrain_ingest(args: dict, **kwargs) -> str:
    tool_name = str(kwargs.pop("_tool_name", "gbrain_ingest"))
    compatibility_alias = bool(kwargs.pop("_compatibility_alias", False))
    warnings = []
    if compatibility_alias:
        warnings.append("obsidian_ingest is a compatibility alias; use gbrain_ingest for new calls")
    try:
        from ingestion.pipeline import ingest
        from ingestion.schema import IngestInput
        from maintenance.gbrain_sync import sync as gbrain_sync

        content = str(args.get("content") or "").strip()
        if not content:
            return _json({
                "ok": False,
                "status": "error",
                "dry_run": bool(args.get("dry_run", False)),
                "output_path": None,
                "error": "content is required",
                "warnings": warnings,
                "tool": tool_name,
                "canonical_tool": "gbrain_ingest",
                "compatibility_alias": compatibility_alias,
            })

        payload = {
            "source_type": args.get("source_type") or "text",
            "source_app": args.get("source_app") or "hermes_plugin",
            "captured_at": args.get("captured_at") or datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
            "title": args.get("title") or content[:72],
            "content": content,
            "attachments": args.get("attachments") or [],
            "metadata": args.get("metadata") or {},
        }
        old_store_low = os.environ.get("STORE_LOW_VALUE_TO_INBOX")
        old_vault = os.environ.get("OBSIDIAN_VAULT_PATH")
        old_dry_run = os.environ.get("GBRAIN_DRY_RUN")
        os.environ["STORE_LOW_VALUE_TO_INBOX"] = "true"
        os.environ["OBSIDIAN_VAULT_PATH"] = _default_vault(args.get("vault_path"))
        if bool(args.get("dry_run", False)):
            os.environ["GBRAIN_DRY_RUN"] = "true"
        try:
            result = ingest(IngestInput.from_payload(payload))
        finally:
            if old_store_low is None:
                os.environ.pop("STORE_LOW_VALUE_TO_INBOX", None)
            else:
                os.environ["STORE_LOW_VALUE_TO_INBOX"] = old_store_low
            if old_vault is None:
                os.environ.pop("OBSIDIAN_VAULT_PATH", None)
            else:
                os.environ["OBSIDIAN_VAULT_PATH"] = old_vault
            if old_dry_run is None:
                os.environ.pop("GBRAIN_DRY_RUN", None)
            else:
                os.environ["GBRAIN_DRY_RUN"] = old_dry_run

        gbrain_result = None
        if result.should_store and not result.dry_run and bool(args.get("sync_gbrain", True)):
            gbrain_result = gbrain_sync(_default_vault())

        return _json(
            {
                "ok": bool(result.should_store),
                "status": result.status,
                "dry_run": result.dry_run,
                "output_path": result.output_path,
                "error": None,
                "warnings": warnings,
                "tool": tool_name,
                "canonical_tool": "gbrain_ingest",
                "compatibility_alias": compatibility_alias,
                "note_type": result.note_type,
                "score": result.score,
                "review_status": result.review_status,
                "sensitivity": result.sensitivity,
                "confidence": result.confidence,
                "suggested_folder": result.suggested_folder,
                "final_folder": result.final_folder,
                "duplicate_of": result.duplicate_of,
                "processing_log_path": result.processing_log_path,
                "action_items": result.action_items,
                "entities": result.entities,
                "tags": result.tags,
                "gbrain": gbrain_result,
            }
        )
    except Exception as exc:
        return _json({
            "ok": False,
            "status": "error",
            "dry_run": bool(args.get("dry_run", False)) if isinstance(args, dict) else False,
            "output_path": None,
            "error": str(exc),
            "warnings": warnings,
            "tool": tool_name,
            "canonical_tool": "gbrain_ingest",
            "compatibility_alias": compatibility_alias,
        })


def obsidian_ingest(args: dict, **kwargs) -> str:
    kwargs["_tool_name"] = "obsidian_ingest"
    kwargs["_compatibility_alias"] = True
    return gbrain_ingest(args, **kwargs)


def gbrain_import(args: dict, **kwargs) -> str:
    try:
        from maintenance.gbrain_sync import sync

        result = sync(_default_vault(args.get("vault_path")))
        return _json(result)
    except Exception as exc:
        return _json({"ok": False, "error": str(exc)})


def gbrain_maintain(args: dict | None = None, **kwargs) -> str:
    try:
        from maintenance.gbrain_maintain import run_maintenance

        return _json({"ok": True, "results": run_maintenance()})
    except Exception as exc:
        return _json({"ok": False, "error": str(exc)})


def gbrain_query(args: dict, **kwargs) -> str:
    from maintenance.gbrain_cli import run_gbrain_command

    query = str(args.get("query") or "").strip()
    if not query:
        return _json({"ok": False, "error": "query is required"})
    return _json(run_gbrain_command(["query", query], command_timeout_seconds=120))
