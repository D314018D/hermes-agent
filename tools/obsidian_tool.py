"""Obsidian vault tools.

Provides a dedicated function tool for writing Markdown notes into the local
Obsidian vault, so messaging agents do not misuse ``send_message`` with an
``obsidian`` target.
"""

from __future__ import annotations

import os
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from tools.registry import registry


def _coerce_args(args: Any) -> Dict[str, Any]:
    if isinstance(args, dict):
        return args
    if isinstance(args, str):
        try:
            parsed = json.loads(args)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            return {"content": args}
    return {}


def _coerce_bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() not in {"0", "false", "no", "off"}
    return bool(value)


def _vault_root() -> Path:
    raw = os.environ.get("OBSIDIAN_VAULT_PATH") or "/Users/rl_home/Documents/Codex/Hermes Agent/integrations/gbrain-obsidian/obsidian-vault"
    return Path(raw).expanduser().resolve()


def _safe_note_path(path: Optional[str], title: Optional[str]) -> Path:
    vault = _vault_root()
    raw = (path or "").strip()
    if not raw:
        name = (title or "Untitled Note").strip()
        name = re.sub(r"[/:\\]+", " - ", name).strip() or "Untitled Note"
        title_lower = name.lower()
        # Match the starter vault's domain folders. Meeting-style notes should
        # be visible under 04-meetings instead of disappearing into brain/inbox.
        if any(token in title_lower for token in ("meeting", "meetings", "会议", "会", "截图")):
            raw = f"04-meetings/{name}.md"
        else:
            raw = f"00-inbox/{name}.md"
    if raw.endswith("/"):
        name = (title or "Untitled Note").strip()
        name = re.sub(r"[/:\\]+", " - ", name).strip() or "Untitled Note"
        raw = f"{raw}{name}.md"
    if not raw.lower().endswith(".md"):
        raw += ".md"

    candidate = Path(raw).expanduser()
    if not candidate.is_absolute():
        candidate = vault / candidate
    resolved = candidate.resolve()
    try:
        resolved.relative_to(vault)
    except ValueError as exc:
        raise ValueError(f"Refusing to write outside Obsidian vault: {resolved}") from exc
    return resolved


def _copy_attachment(src: str, note_path: Path) -> str:
    source = Path(src).expanduser()
    if not source.is_file():
        raise FileNotFoundError(f"Attachment not found: {src}")
    vault = _vault_root()
    attachments_dir = vault / "attachments" / "telegram"
    attachments_dir.mkdir(parents=True, exist_ok=True)
    dest = attachments_dir / source.name
    if dest.exists():
        stem = dest.stem
        suffix = dest.suffix
        dest = attachments_dir / f"{stem}-{datetime.now().strftime('%Y%m%d%H%M%S')}{suffix}"
    shutil.copy2(source, dest)
    return f"telegram/{dest.name}"


def _write_with_gbrain_ingestion(
    *,
    title: Optional[str],
    content: str,
    attachments: List[str],
) -> Optional[Dict[str, Any]]:
    starter = Path("/Users/rl_home/Documents/Codex/Hermes Agent/integrations/gbrain-obsidian")
    if not starter.is_dir():
        return None
    starter_str = str(starter)
    if starter_str not in sys.path:
        sys.path.insert(0, starter_str)
    try:
        from ingestion.pipeline import ingest
        from ingestion.schema import IngestInput
    except Exception:
        return None

    item = IngestInput(
        source_type="text",
        source_app="hermes",
        captured_at=datetime.now().astimezone().isoformat(timespec="seconds"),
        title=(title or "Untitled Note").strip() or "Untitled Note",
        content=content or "",
        attachments=attachments,
        metadata={"ingested_by": "gbrain_ingest", "render_target": "obsidian"},
    )
    old_vault = os.environ.get("OBSIDIAN_VAULT_PATH")
    os.environ["OBSIDIAN_VAULT_PATH"] = str(_vault_root())
    try:
        result = ingest(item)
    except Exception:
        return None
    finally:
        if old_vault is None:
            os.environ.pop("OBSIDIAN_VAULT_PATH", None)
        else:
            os.environ["OBSIDIAN_VAULT_PATH"] = old_vault
    return {
        "success": bool(result.output_path),
        "action": "ingested" if result.output_path else "skipped",
        "path": result.output_path,
        "vault": str(_vault_root()),
        "method": "gbrain_ingestion",
        "note_type": result.note_type,
        "score": result.score,
        "summary": result.summary,
        "attachments": attachments,
    }


def gbrain_ingest(
    *,
    title: Optional[str],
    content: str,
    source_type: str = "text",
    source_app: str = "hermes_gateway",
    captured_at: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    attachments: Optional[List[str]] = None,
    sync_gbrain: bool = True,
    build_indexes: bool = True,
) -> Dict[str, Any]:
    starter = Path("/Users/rl_home/Documents/Codex/Hermes Agent/integrations/gbrain-obsidian")
    if not starter.is_dir():
        return {"success": False, "entrypoint": "gbrain_ingest", "error": "GBrain starter project not found"}
    starter_str = str(starter)
    if starter_str not in sys.path:
        sys.path.insert(0, starter_str)

    copied_attachments: List[str] = []
    note_path = _safe_note_path(None, title)
    for attachment in attachments or []:
        copied_attachments.append(_copy_attachment(attachment, note_path))

    try:
        from ingestion.pipeline import ingest
        from ingestion.schema import IngestInput
        from maintenance.gbrain_sync import sync as gbrain_sync
        from maintenance.gbrain_maintain import run_maintenance
    except Exception as exc:
        return {"success": False, "entrypoint": "gbrain_ingest", "error": str(exc)}

    meta = {str(k): str(v) for k, v in (metadata or {}).items()}
    meta.setdefault("ingested_by", "gbrain_ingest")
    meta.setdefault("render_target", "obsidian")
    item = IngestInput(
        source_type=source_type if source_type in {"text", "voice", "file", "email"} else "text",
        source_app=source_app or "hermes_gateway",
        captured_at=captured_at or datetime.now().astimezone().isoformat(timespec="seconds"),
        title=(title or "Untitled Knowledge Capture").strip() or "Untitled Knowledge Capture",
        content=content or "",
        attachments=copied_attachments,
        metadata=meta,
    )

    old_vault = os.environ.get("OBSIDIAN_VAULT_PATH")
    old_store_low = os.environ.get("STORE_LOW_VALUE_TO_INBOX")
    os.environ["OBSIDIAN_VAULT_PATH"] = str(_vault_root())
    os.environ["STORE_LOW_VALUE_TO_INBOX"] = "true"
    try:
        result = ingest(item)
        gbrain_import_result = gbrain_sync(str(_vault_root())) if result.should_store and sync_gbrain else None
        gbrain_maintain_result = run_maintenance() if result.should_store and build_indexes else None
    except Exception as exc:
        return {"success": False, "entrypoint": "gbrain_ingest", "error": str(exc)}
    finally:
        if old_vault is None:
            os.environ.pop("OBSIDIAN_VAULT_PATH", None)
        else:
            os.environ["OBSIDIAN_VAULT_PATH"] = old_vault
        if old_store_low is None:
            os.environ.pop("STORE_LOW_VALUE_TO_INBOX", None)
        else:
            os.environ["STORE_LOW_VALUE_TO_INBOX"] = old_store_low

    return {
        "success": bool(result.should_store),
        "entrypoint": "gbrain_ingest",
        "stage": "gbrain_core_to_obsidian_render",
        "action": "ingested" if result.output_path else "skipped",
        "path": result.output_path,
        "rendered_markdown_path": result.output_path,
        "vault": str(_vault_root()),
        "method": "gbrain_ingestion",
        "note_type": result.note_type,
        "classification_confidence": result.classification_confidence,
        "classification_reason": result.classification_reason,
        "score": result.score,
        "summary": result.summary,
        "entities": result.entities,
        "relations": [],
        "tags": result.tags,
        "attachments": copied_attachments,
        "gbrain_import": gbrain_import_result,
        "gbrain_maintain": gbrain_maintain_result,
    }


def obsidian_write_note(
    *,
    title: Optional[str],
    content: str,
    path: Optional[str] = None,
    append: bool = False,
    attachments: Optional[List[str]] = None,
) -> Dict[str, Any]:
    note_path = _safe_note_path(path, title)
    note_path.parent.mkdir(parents=True, exist_ok=True)

    body = content or ""
    copied_attachments: List[str] = []
    for attachment in attachments or []:
        name = _copy_attachment(attachment, note_path)
        copied_attachments.append(name)
        if f"[[{name}]]" not in body:
            body += f"\n\n![[{name}]]\n"

    if not append:
        gbrain_result = _write_with_gbrain_ingestion(
            title=title,
            content=body,
            attachments=copied_attachments,
        )
        if gbrain_result is not None:
            return gbrain_result

    cli_result = _write_with_obsidian_cli(note_path, title, body, append)
    if cli_result is not None:
        cli_result["attachments"] = copied_attachments
        return cli_result

    if append and note_path.exists():
        with note_path.open("a", encoding="utf-8") as fh:
            if not body.startswith("\n"):
                fh.write("\n\n")
            fh.write(body.rstrip() + "\n")
        action = "appended"
    else:
        note_path.write_text(body.rstrip() + "\n", encoding="utf-8")
        action = "written"

    return {
        "success": True,
        "action": action,
        "path": str(note_path),
        "vault": str(_vault_root()),
        "attachments": copied_attachments,
    }


def _write_with_obsidian_cli(
    note_path: Path,
    title: Optional[str],
    body: str,
    append: bool,
) -> Optional[Dict[str, Any]]:
    """Write through the Obsidian CLI when it is available and responsive.

    The CLI talks to a running Obsidian instance. If Obsidian is closed or the
    command fails, return None so the local vault-file fallback can still finish
    the user's request.
    """
    obsidian_bin = shutil.which("obsidian")
    if not obsidian_bin:
        return None

    vault = _vault_root()
    try:
        rel_path = str(note_path.relative_to(vault))
    except ValueError:
        return None

    if append:
        cmd = [obsidian_bin, "append", f"path={rel_path}", f"content={body.rstrip()}"]
    else:
        name = title or note_path.stem
        cmd = [
            obsidian_bin,
            "create",
            f"name={name}",
            f"path={rel_path}",
            f"content={body.rstrip()}",
            "overwrite",
            "silent",
        ]

    try:
        result = subprocess.run(
            cmd,
            text=True,
            capture_output=True,
            timeout=20,
            check=False,
        )
    except Exception:
        return None

    if result.returncode != 0:
        return None
    if not note_path.exists():
        return None

    return {
        "success": True,
        "action": "appended" if append else "written",
        "path": str(note_path),
        "vault": str(vault),
        "method": "obsidian_cli",
        "stdout": result.stdout.strip()[-1000:],
    }


OBSIDIAN_WRITE_NOTE_SCHEMA = {
    "name": "obsidian_write_note",
    "description": (
        "Compatibility path for writing a rendered Markdown note after GBrain processing. "
        "Prefer gbrain_ingest when the user asks to save business material, durable "
        "knowledge, memory, or knowledge-base content."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Human-readable note title. Used for default filename if path is omitted.",
            },
            "path": {
                "type": "string",
                "description": (
                    "Vault-relative Markdown path, e.g. "
                    "'04-meetings/2026年四月份销售管理会.md'. "
                    "Absolute paths are allowed only inside the configured vault."
                ),
            },
            "content": {
                "type": "string",
                "description": "Complete Markdown content to write or append.",
            },
            "append": {
                "type": "boolean",
                "description": "Append to an existing note instead of replacing it.",
                "default": False,
            },
            "attachments": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "Optional local file paths to copy into the vault attachments folder. "
                    "Copied images are embedded with Obsidian wikilinks."
                ),
            },
        },
        "required": ["content"],
    },
}


GBRAIN_INGEST_SCHEMA = {
    "name": "gbrain_ingest",
    "description": (
        "Canonical GBrain-first knowledge-base ingestion. Use for Telegram, WeChat, "
        "voice transcripts, files, business ideas, project facts, meetings, decisions, "
        "or anything the user asks to save into the knowledge base. The content is "
        "processed by GBrain and rendered into Obsidian Markdown."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Short title for the durable memory item."},
            "content": {"type": "string", "description": "Normalized text, transcript, or parsed document content to ingest."},
            "source_type": {"type": "string", "enum": ["text", "voice", "file", "email"], "description": "Input modality."},
            "source_app": {"type": "string", "description": "Source platform, e.g. telegram, weixin, webui."},
            "captured_at": {"type": "string", "description": "ISO timestamp if known."},
            "metadata": {"type": "object", "description": "Small source metadata object such as chat id, user id, or message id."},
            "attachments": {"type": "array", "items": {"type": "string"}, "description": "Optional local file paths copied into the vault attachment area."},
            "sync_gbrain": {"type": "boolean", "description": "Import the rendered vault content into GBrain after ingestion."},
            "build_indexes": {"type": "boolean", "description": "Run GBrain maintenance for embeddings, links, timeline, and graph extraction."},
        },
        "required": ["content"],
    },
}


def _handle_gbrain_ingest(args: Any, **kw: Any) -> str:
    _args = _coerce_args(args)
    result = gbrain_ingest(
        title=_args.get("title"),
        content=_args.get("content", ""),
        source_type=_args.get("source_type") or "text",
        source_app=_args.get("source_app") or "hermes_gateway",
        captured_at=_args.get("captured_at"),
        metadata=_args.get("metadata") or {},
        attachments=_args.get("attachments") or [],
        sync_gbrain=_coerce_bool(_args.get("sync_gbrain"), True),
        build_indexes=_coerce_bool(_args.get("build_indexes"), True),
    )
    return json.dumps(result, ensure_ascii=False)


def _handle_obsidian_write_note(args: Any, **kw: Any) -> str:
    _args = _coerce_args(args)
    result = obsidian_write_note(
        title=_args.get("title"),
        path=_args.get("path"),
        content=_args.get("content", ""),
        append=_args.get("append", False),
        attachments=_args.get("attachments") or [],
    )
    return json.dumps(result, ensure_ascii=False)



registry.register(
    name="gbrain_ingest",
    toolset="gbrain",
    schema=GBRAIN_INGEST_SCHEMA,
    handler=_handle_gbrain_ingest,
    emoji="🧠",
)

registry.register(
    name="obsidian_write_note",
    toolset="obsidian",
    schema=OBSIDIAN_WRITE_NOTE_SCHEMA,
    handler=_handle_obsidian_write_note,
    emoji="🪨",
)
