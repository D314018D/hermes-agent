"""Convert local documents into normalized Markdown for Hermes workflows."""

from __future__ import annotations

import json
import mimetypes
from pathlib import Path
from typing import Any, Dict, Optional


_DEFAULT_INSTALL_HINT = "pip install 'markitdown[pdf,docx,pptx,xlsx,xls]'"


def _guess_media_type(path: Path) -> str:
    guessed, _ = mimetypes.guess_type(path.name)
    return guessed or "application/octet-stream"


def _trim_text(text: str, max_chars: Optional[int]) -> str:
    if max_chars is None or max_chars <= 0 or len(text) <= max_chars:
        return text
    return text[:max_chars]


def normalize_document_to_markdown(
    file_path: str,
    *,
    max_chars: Optional[int] = None,
    install_hint: str = _DEFAULT_INSTALL_HINT,
) -> Dict[str, Any]:
    """Convert a local file into normalized Markdown using MarkItDown."""
    path = Path(file_path).expanduser()

    if not path.exists():
        return {
            "success": False,
            "error": f"File not found: {path}",
            "file_path": str(path),
        }

    if not path.is_file():
        return {
            "success": False,
            "error": f"Path is not a file: {path}",
            "file_path": str(path),
        }

    try:
        from markitdown import MarkItDown
    except ImportError:
        return {
            "success": False,
            "error": "markitdown is not installed",
            "file_path": str(path),
            "install_hint": install_hint,
        }

    try:
        converter = MarkItDown()
        result = converter.convert(str(path))
        markdown = getattr(result, "text_content", "") or ""
        normalized = markdown.strip()
        trimmed = _trim_text(normalized, max_chars)
        was_truncated = trimmed != normalized

        return {
            "success": True,
            "file_path": str(path.resolve()),
            "file_name": path.name,
            "extension": path.suffix.lower(),
            "media_type": _guess_media_type(path),
            "markdown": trimmed,
            "markdown_char_count": len(normalized),
            "returned_char_count": len(trimmed),
            "truncated": was_truncated,
            "converter": "microsoft-markitdown",
        }
    except Exception as exc:
        return {
            "success": False,
            "error": f"{type(exc).__name__}: {exc}",
            "file_path": str(path.resolve()),
        }


def document_normalization_tool(
    file_path: str,
    max_chars: Optional[int] = 12000,
) -> str:
    """Hermes-compatible tool wrapper that returns JSON."""
    payload = normalize_document_to_markdown(
        file_path=file_path,
        max_chars=max_chars,
    )
    return json.dumps(payload, ensure_ascii=False)
