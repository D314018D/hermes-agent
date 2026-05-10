#!/usr/bin/env python3
"""
apple_notes tool for Apple Notes.

Provides a native Hermes tool wrapper around Apple Notes via osascript so
models can list, search, view, create, append to, replace, and delete notes
without relying on memo's interactive CLI flows.
"""

from __future__ import annotations

import html
import json
import platform
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from tools.registry import registry, tool_error, tool_result


NOTES_APP_PATH = Path("/System/Applications/Notes.app")
FIELD_DELIM = chr(31)
RECORD_DELIM = chr(30)
RECENTLY_DELETED_NAMES = {
    "Recently Deleted",
    "Nylig slettet",
    "Senast raderade",
    "Senest slettet",
    "Zuletzt gelöscht",
    "Supprimes recemment",
    "Supprimés récemment",
    "Eliminados recientemente",
    "Eliminati di recente",
    "Recent verwijderd",
    "Ostatnio usuniete",
    "Ostatnio usunięte",
    "Недавно удалённые",
    "Apagados recentemente",
    "Apagadas recentemente",
    "最近删除",
    "最近刪除",
    "最近削除した項目",
    "최근 삭제된 항목",
    "Son Silinenler",
    "Äskettäin poistetut",
    "Nedavno smazane",
    "Nedávno smazané",
    "Πρόσφατα διαγραμμένα",
    "Nemreg toroltek",
    "Nemrég töröltek",
    "Sterse recent",
    "Șterse recent",
    "Nedavno vymazane",
    "Nedávno vymazané",
    "เพิ่งลบ",
    "Đã xóa gần đây",
    "Нещодавно видалені",
}


def check_apple_notes_requirements() -> bool:
    return (
        platform.system() == "Darwin"
        and shutil.which("osascript") is not None
        and NOTES_APP_PATH.exists()
    )


def _clean_str(value: Any) -> str:
    return str(value or "").strip()


def _strip_html(text: str) -> str:
    raw = text or ""
    raw = re.sub(r"(?is)<br\s*/?>", "\n", raw)
    raw = re.sub(r"(?is)</p\s*>", "\n", raw)
    raw = re.sub(r"(?is)<[^>]+>", "", raw)
    raw = html.unescape(raw)
    raw = raw.replace("\r", "")
    raw = re.sub(r"\n{3,}", "\n\n", raw)
    return raw.strip()


def _run_osascript(script: str, args: list[str], timeout: int = 45) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["osascript", "-", *args],
        input=script,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def _looks_like_auth_error(text: str) -> bool:
    raw = (text or "").lower()
    return any(
        marker in raw
        for marker in (
            "not authorized",
            "not permitted",
            "permission",
            "automation",
            "not allowed assistive access",
            "(-1743)",
        )
    )


def _list_script() -> str:
    return r'''
on run argv
    set folderFilter to item 1 of argv
    set includeBodyFlag to item 2 of argv
    set includeBody to includeBodyFlag is "1"
    set fieldDelim to character id 31
    set recordDelim to character id 30
    set deletedTranslations to {"Recently Deleted", "Nylig slettet", "Senast raderade", "Senest slettet", "Zuletzt gelöscht", "Supprimés récemment", "Eliminados recientemente", "Eliminati di recente", "Recent verwijderd", "Ostatnio usunięte", "Недавно удалённые", "Apagados recentemente", "Apagadas recentemente", "最近删除", "最近刪除", "最近削除した項目", "최근 삭제된 항목", "Son Silinenler", "Äskettäin poistetut", "Nedávno smazané", "Πρόσφατα διαγραμμένα", "Nemrég töröltek", "Șterse recent", "Nedávno vymazané", "เพิ่งลบ", "Đã xóa gần đây", "Нещодавно видалені"}
    set rows to {}
    tell application "Notes"
        repeat with eachFolder in folders
            set folderName to name of eachFolder
            if folderName is not in deletedTranslations then
                if folderFilter is "" or folderName is equal to folderFilter then
                    repeat with eachNote in notes of eachFolder
                        set noteId to id of eachNote
                        set noteName to name of eachNote
                        if includeBody then
                            set noteBody to body of eachNote
                        else
                            set noteBody to ""
                        end if
                        set end of rows to noteId & fieldDelim & folderName & fieldDelim & noteName & fieldDelim & noteBody
                    end repeat
                end if
            end if
        end repeat
    end tell
    set AppleScript's text item delimiters to recordDelim
    set outputText to rows as string
    set AppleScript's text item delimiters to ""
    return outputText
end run
'''


def _folders_script() -> str:
    return r'''
on run argv
    set recordDelim to character id 30
    set deletedTranslations to {"Recently Deleted", "Nylig slettet", "Senast raderade", "Senest slettet", "Zuletzt gelöscht", "Supprimés récemment", "Eliminados recientemente", "Eliminati di recente", "Recent verwijderd", "Ostatnio usunięte", "Недавно удалённые", "Apagados recentemente", "Apagadas recentemente", "最近删除", "最近刪除", "最近削除した項目", "최근 삭제된 항목", "Son Silinenler", "Äskettäin poistetut", "Nedávno smazané", "Πρόσφατα διαγραμμένα", "Nemrég töröltek", "Șterse recent", "Nedávno vymazané", "เพิ่งลบ", "Đã xóa gần đây", "Нещодавно видалені"}
    set rows to {}
    tell application "Notes"
        repeat with eachFolder in folders
            set folderName to name of eachFolder
            if folderName is not in deletedTranslations then
                set end of rows to folderName
            end if
        end repeat
    end tell
    set AppleScript's text item delimiters to recordDelim
    set outputText to rows as string
    set AppleScript's text item delimiters to ""
    return outputText
end run
'''


def _create_script() -> str:
    return r'''
on run argv
    set folderName to item 1 of argv
    set noteTitle to item 2 of argv
    set noteBody to item 3 of argv
    tell application "Notes"
        if folderName is not "" then
            set targetFolder to first folder whose name is folderName
        else
            set targetFolder to first folder
        end if
        set createdNote to make new note at targetFolder with properties {name:noteTitle, body:noteBody}
        return id of createdNote
    end tell
end run
'''


def _update_script(mode: str) -> str:
    body_statement = (
        'set body of targetNote to ((body of targetNote) & updateBody)'
        if mode == "append"
        else 'set body of targetNote to updateBody'
    )
    return f'''
on run argv
    set noteId to item 1 of argv
    set updateTitle to item 2 of argv
    set updateBody to item 3 of argv
    tell application "Notes"
        set targetNote to first note whose id is noteId
        if updateTitle is not "" then
            set name of targetNote to updateTitle
        end if
        if updateBody is not "" then
            {body_statement}
        end if
        return id of targetNote
    end tell
end run
'''


def _delete_script() -> str:
    return r'''
on run argv
    set noteId to item 1 of argv
    tell application "Notes"
        set targetNote to first note whose id is noteId
        delete targetNote
    end tell
    return noteId
end run
'''


def _parse_note_rows(raw: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for idx, line in enumerate((raw or "").split(RECORD_DELIM), start=1):
        if not line:
            continue
        parts = line.split(FIELD_DELIM, 3)
        if len(parts) < 4:
            continue
        note_id, folder, title, body_html = parts
        body_text = _strip_html(body_html)
        rows.append(
            {
                "index": idx,
                "id": note_id,
                "folder": folder,
                "title": title,
                "body_html": body_html,
                "body_text": body_text,
            }
        )
    return rows


def _find_note(notes: list[dict[str, str]], note_id: str, note_index: int) -> dict[str, str] | None:
    if note_id:
        for note in notes:
            if note["id"] == note_id or note["id"].startswith(note_id):
                return note
    if note_index > 0:
        for note in notes:
            if note["index"] == note_index:
                return note
    return None


def _fetch_notes(folder: str = "", include_body: bool = True) -> tuple[list[dict[str, str]], subprocess.CompletedProcess[str]]:
    proc = _run_osascript(_list_script(), [folder, "1" if include_body else "0"])
    rows = _parse_note_rows(proc.stdout.strip()) if proc.returncode == 0 else []
    return rows, proc


def _filter_notes(notes: list[dict[str, str]], query: str, limit: int) -> list[dict[str, Any]]:
    filtered = notes
    if query:
        q = query.lower()
        filtered = [
            note
            for note in notes
            if q in note["title"].lower() or q in note["body_text"].lower() or q in note["folder"].lower()
        ]
    result: list[dict[str, Any]] = []
    for note in filtered[: max(limit, 1)]:
        result.append(
            {
                "index": note["index"],
                "id": note["id"],
                "folder": note["folder"],
                "title": note["title"],
                "snippet": note["body_text"][:240],
            }
        )
    return result


def apple_notes_tool(
    action: str,
    folder: str = "",
    query: str = "",
    title: str = "",
    body: str = "",
    note_id: str = "",
    note_index: int = 0,
    limit: int = 20,
) -> str:
    action = _clean_str(action).lower()
    folder = _clean_str(folder)
    query = _clean_str(query)
    title = _clean_str(title)
    note_id = _clean_str(note_id)
    if action not in {"list", "folders", "view", "create", "append", "replace", "delete"}:
        return tool_error("Unsupported Apple Notes action.", action=action)

    if action == "folders":
        proc = _run_osascript(_folders_script(), [])
        output = proc.stdout.strip() or proc.stderr.strip()
        if proc.returncode != 0:
            return tool_result(
                success=False,
                action=action,
                command=["osascript", "-", "[folders script]"],
                exit_code=proc.returncode,
                output=output,
                auth_required=_looks_like_auth_error(output),
            )
        folders = [line for line in output.split(RECORD_DELIM) if line and line not in RECENTLY_DELETED_NAMES]
        return tool_result(success=True, action=action, folders=folders, count=len(folders))

    if action == "list":
        notes, proc = _fetch_notes(folder=folder, include_body=True)
        output = proc.stdout.strip() or proc.stderr.strip()
        if proc.returncode != 0:
            return tool_result(
                success=False,
                action=action,
                command=["osascript", "-", "[list script]", folder],
                exit_code=proc.returncode,
                output=output,
                auth_required=_looks_like_auth_error(output),
            )
        filtered = _filter_notes(notes, query=query, limit=limit)
        return tool_result(
            success=True,
            action=action,
            folder=folder or None,
            query=query or None,
            count=len(filtered),
            total=len(notes),
            notes=filtered,
        )

    notes, list_proc = _fetch_notes(folder=folder, include_body=True)
    list_output = list_proc.stdout.strip() or list_proc.stderr.strip()
    if list_proc.returncode != 0:
        return tool_result(
            success=False,
            action=action,
            command=["osascript", "-", "[list script]", folder],
            exit_code=list_proc.returncode,
            output=list_output,
            auth_required=_looks_like_auth_error(list_output),
        )

    target = _find_note(notes, note_id=note_id, note_index=note_index)
    if action in {"view", "append", "replace", "delete"} and not target:
        return tool_error(
            "note_id or note_index did not resolve to a note.",
            action=action,
            note_id=note_id or None,
            note_index=note_index or None,
        )

    if action == "view":
        return tool_result(
            success=True,
            action=action,
            note={
                "index": target["index"],
                "id": target["id"],
                "folder": target["folder"],
                "title": target["title"],
                "body": target["body_text"],
                "body_html": target["body_html"],
            },
        )

    if action == "create":
        if not title:
            return tool_error("title is required for create.")
        proc = _run_osascript(_create_script(), [folder, title, body])
        output = proc.stdout.strip() or proc.stderr.strip()
        created_id = output if proc.returncode == 0 else ""
        verification = None
        if created_id:
            refreshed, _ = _fetch_notes(folder=folder, include_body=True)
            created = _find_note(refreshed, note_id=created_id, note_index=0)
            if created:
                verification = {
                    "id": created["id"],
                    "folder": created["folder"],
                    "title": created["title"],
                    "snippet": created["body_text"][:240],
                }
        return tool_result(
            success=proc.returncode == 0,
            action=action,
            command=["osascript", "-", "[create script]", folder, title],
            exit_code=proc.returncode,
            output=output,
            title=title,
            folder=folder or None,
            note_id=created_id or None,
            verification=verification,
            auth_required=_looks_like_auth_error(output),
        )

    if action in {"append", "replace"}:
        if not body and not title:
            return tool_error("title and/or body is required for append/replace.", action=action)
        proc = _run_osascript(_update_script(action), [target["id"], title, body])
        output = proc.stdout.strip() or proc.stderr.strip()
        verification = None
        if proc.returncode == 0:
            refreshed, _ = _fetch_notes(folder=target["folder"], include_body=True)
            updated = _find_note(refreshed, note_id=target["id"], note_index=0)
            if updated:
                verification = {
                    "id": updated["id"],
                    "title": updated["title"],
                    "snippet": updated["body_text"][:240],
                }
        return tool_result(
            success=proc.returncode == 0,
            action=action,
            command=["osascript", "-", "[update script]", target["id"]],
            exit_code=proc.returncode,
            output=output,
            note_id=target["id"],
            note_index=target["index"],
            verification=verification,
            auth_required=_looks_like_auth_error(output),
        )

    proc = _run_osascript(_delete_script(), [target["id"]])
    output = proc.stdout.strip() or proc.stderr.strip()
    return tool_result(
        success=proc.returncode == 0,
        action=action,
        command=["osascript", "-", "[delete script]", target["id"]],
        exit_code=proc.returncode,
        output=output,
        note_id=target["id"],
        note_index=target["index"],
        title=target["title"],
        folder=target["folder"],
        auth_required=_looks_like_auth_error(output),
    )


APPLE_NOTES_SCHEMA = {
    "name": "apple_notes",
    "description": (
        "Manage Apple Notes on macOS. Supports listing folders/notes, searching, "
        "viewing a note, creating notes, appending/replacing note content, and deleting notes."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["list", "folders", "view", "create", "append", "replace", "delete"],
                "description": "The Apple Notes action to run.",
            },
            "folder": {
                "type": "string",
                "description": "Optional folder filter or destination folder.",
            },
            "query": {
                "type": "string",
                "description": "Optional case-insensitive search string for list.",
            },
            "title": {
                "type": "string",
                "description": "Note title for create or title update.",
            },
            "body": {
                "type": "string",
                "description": "Body content for create, append, or replace.",
            },
            "note_id": {
                "type": "string",
                "description": "Exact note id or id prefix for view/update/delete.",
            },
            "note_index": {
                "type": "integer",
                "description": "1-based note index from the list action as an alternative selector.",
                "default": 0,
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of notes to return for list.",
                "default": 20,
            },
        },
        "required": ["action"],
    },
}


registry.register(
    name="apple_notes",
    toolset="terminal",
    schema=APPLE_NOTES_SCHEMA,
    handler=lambda args, **kw: apple_notes_tool(
        action=args.get("action", ""),
        folder=args.get("folder", ""),
        query=args.get("query", ""),
        title=args.get("title", ""),
        body=args.get("body", ""),
        note_id=args.get("note_id", ""),
        note_index=int(args.get("note_index", 0) or 0),
        limit=int(args.get("limit", 20) or 20),
    ),
    check_fn=check_apple_notes_requirements,
    emoji="📝",
)
