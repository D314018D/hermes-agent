#!/usr/bin/env python3
"""
remindctl tool for Apple Reminders.

Provides a native Hermes tool wrapper around the `remindctl` CLI so models can
create, inspect, complete, and delete Apple Reminders without guessing at a
non-existent tool interface.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, List

from tools.registry import registry, tool_error, tool_result


REMINDCTL_BIN = shutil.which("remindctl") or "/opt/homebrew/bin/remindctl"
BROKER_PATH = Path("/Users/rl_home/.hermes/hermes-agent/tools/remindctl_terminal_broker.py")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TIME_RE = re.compile(r"^\d{1,2}:\d{2}$")


def check_remindctl_requirements() -> bool:
    return shutil.which("remindctl") is not None or shutil.which("/opt/homebrew/bin/remindctl") is not None


def _run_remindctl(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [REMINDCTL_BIN, *args],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


def _run_broker(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(BROKER_PATH), *args],
        capture_output=True,
        text=True,
        timeout=45,
        check=False,
    )


def _clean_str(value: Any) -> str:
    return str(value or "").strip()


def _normalize_due(due: str, date_value: str, time_value: str) -> str:
    if due:
        return due
    if date_value and time_value:
        return f"{date_value} {time_value}"
    if date_value:
        return date_value
    if time_value:
        today = datetime.now().strftime("%Y-%m-%d")
        return f"{today} {time_value}"
    return ""


def _verification_target(action: str, due: str, date_value: str) -> list[str] | None:
    if action != "add":
        return None
    target = due or date_value
    if not target:
        return ["today", "--plain"]
    if DATE_RE.match(target):
        return [target, "--plain"]
    if len(target) >= 10 and DATE_RE.match(target[:10]):
        return [target[:10], "--plain"]
    return None


def _collect_ids(raw_ids: Any, reminder_id: str) -> list[str]:
    ids: list[str] = []
    if isinstance(raw_ids, list):
        ids.extend(_clean_str(item) for item in raw_ids)
    elif raw_ids not in (None, ""):
        ids.append(_clean_str(raw_ids))
    if reminder_id:
        ids.append(reminder_id)
    return [item for item in ids if item]


def _looks_like_tcc_or_auth_error(text: str) -> bool:
    raw = (text or "").lower()
    return any(
        marker in raw
        for marker in (
            "not determined",
            "denied",
            "mach error",
            "tcc",
            "privacy",
            "authorization",
        )
    )


def remindctl_tool(
    action: str,
    filter: str = "",
    title: str = "",
    due: str = "",
    time: str = "",
    date: str = "",
    list_name: str = "",
    reminder_id: str = "",
    reminder_ids: Any = None,
    notes: str = "",
    priority: str = "",
    rename: str = "",
    create_list: bool = False,
    clear_due: bool = False,
    mark_complete: bool = False,
    mark_incomplete: bool = False,
    delete_list: bool = False,
    force: bool = False,
    output: str = "plain",
    verify: bool = True,
) -> str:
    action = _clean_str(action).lower()
    if action not in {
        "show", "add", "list", "authorize", "today", "tomorrow", "week",
        "overdue", "upcoming", "completed", "all", "status", "edit",
        "complete", "delete"
    }:
        return tool_error("Unsupported remindctl action.", action=action)

    filter = _clean_str(filter)
    title = _clean_str(title)
    due = _clean_str(due)
    time = _clean_str(time)
    date = _clean_str(date)
    list_name = _clean_str(list_name)
    reminder_id = _clean_str(reminder_id)
    notes = _clean_str(notes)
    priority = _clean_str(priority).lower()
    rename = _clean_str(rename)
    output = _clean_str(output).lower() or "plain"

    cmd: list[str] = []
    if action == "show":
        cmd = ["show"]
        if filter:
            cmd.append(filter)
        elif date:
            cmd.append(date)
    elif action == "add":
        if not title:
            return tool_error("title is required for add.")
        resolved_due = _normalize_due(due, date, time)
        cmd = ["add", "--title", title]
        if list_name:
            cmd.extend(["--list", list_name])
        if resolved_due:
            cmd.extend(["--due", resolved_due])
    elif action == "authorize":
        cmd = ["authorize"]
    elif action == "list":
        cmd = ["list"]
        if list_name:
            cmd.append(list_name)
        if create_list or (force and not delete_list and not rename):
            cmd.append("--create")
        if rename:
            cmd.extend(["--rename", rename])
        if delete_list:
            cmd.append("--delete")
            if force:
                cmd.append("--force")
    elif action in {"today", "tomorrow", "week", "overdue", "upcoming", "completed", "all"}:
        cmd = ["show", action]
    elif action == "status":
        cmd = ["status"]
    elif action == "edit":
        ids = _collect_ids(reminder_ids, reminder_id)
        if not ids:
            return tool_error("reminder_id or reminder_ids is required for edit.", action=action)
        if len(ids) > 1:
            return tool_error("edit supports only one reminder at a time.", action=action)
        cmd = ["edit", ids[0]]
        resolved_due = _normalize_due(due, date, time)
        if title:
            cmd.extend(["--title", title])
        if list_name:
            cmd.extend(["--list", list_name])
        if resolved_due:
            cmd.extend(["--due", resolved_due])
        if notes:
            cmd.extend(["--notes", notes])
        if priority:
            cmd.extend(["--priority", priority])
        if clear_due:
            cmd.append("--clear-due")
        if mark_complete:
            cmd.append("--complete")
        if mark_incomplete:
            cmd.append("--incomplete")
    elif action in {"complete", "delete"}:
        ids = _collect_ids(reminder_ids, reminder_id)
        if not ids:
            return tool_error("reminder_id or reminder_ids is required for this action.", action=action)
        cmd = [action, *ids]
        if action == "delete" and force:
            cmd.append("--force")
    else:
        cmd = [action]

    if action in {"show", "today", "tomorrow", "week", "overdue", "upcoming", "completed", "all", "list", "edit"}:
        if output == "json":
            cmd.append("--json")
        elif output == "quiet":
            cmd.append("--quiet")
        elif output == "plain":
            cmd.append("--plain")

    proc = _run_remindctl(cmd)
    stdout = proc.stdout.strip()
    stderr = proc.stderr.strip()
    combined = stdout or stderr
    used_broker = False

    if proc.returncode != 0 and _looks_like_tcc_or_auth_error(combined) and BROKER_PATH.exists():
        broker_proc = _run_broker(cmd)
        proc = broker_proc
        stdout = proc.stdout.strip()
        stderr = proc.stderr.strip()
        combined = stdout or stderr
        used_broker = True

    verification: dict[str, Any] | None = None
    verify_args = _verification_target(action, due or _normalize_due("", date, time), date)
    if proc.returncode == 0 and verify and verify_args:
        verify_proc = _run_remindctl(verify_args)
        verification = {
            "command": [REMINDCTL_BIN, *verify_args],
            "exit_code": verify_proc.returncode,
            "output": (verify_proc.stdout or verify_proc.stderr).strip(),
        }

    return tool_result(
        success=proc.returncode == 0,
        action=action,
        command=(["python3", str(BROKER_PATH), *cmd] if used_broker else [REMINDCTL_BIN, *cmd]),
        exit_code=proc.returncode,
        output=combined,
        title=title or None,
        due=_normalize_due(due, date, time) or None,
        list_name=list_name or None,
        used_broker=used_broker,
        verification=verification,
    )


REMINDCTL_SCHEMA = {
    "name": "remindctl",
    "description": (
        "Manage Apple Reminders through the local remindctl CLI. Use this for "
        "Apple Reminder requests from chat or messaging channels. Supports show, "
        "list, add, authorize, status, edit, complete, and delete."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["show", "add", "list", "authorize", "today", "tomorrow", "week", "overdue", "upcoming", "completed", "all", "status", "edit", "complete", "delete"],
                "description": "The remindctl action to run.",
            },
            "filter": {
                "type": "string",
                "description": "Optional show filter such as 'today', 'tomorrow', 'week', 'overdue', 'upcoming', 'completed', 'all', or '2026-05-10'.",
            },
            "title": {
                "type": "string",
                "description": "Reminder title. Required for add.",
            },
            "due": {
                "type": "string",
                "description": "Due date/time such as 'tomorrow', '2026-05-10', or '2026-05-10 18:00'.",
            },
            "date": {
                "type": "string",
                "description": "Optional date component to combine with time, usually YYYY-MM-DD.",
            },
            "time": {
                "type": "string",
                "description": "Optional time component such as '18:00'. If provided without date, today is assumed.",
            },
            "list_name": {
                "type": "string",
                "description": "Reminder list name for add/list.",
            },
            "reminder_id": {
                "type": "string",
                "description": "Single reminder id for complete/delete.",
            },
            "reminder_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Multiple reminder ids for complete/delete.",
            },
            "notes": {
                "type": "string",
                "description": "Reminder notes for edit.",
            },
            "priority": {
                "type": "string",
                "enum": ["none", "low", "medium", "high"],
                "description": "Reminder priority for edit.",
            },
            "rename": {
                "type": "string",
                "description": "New list name for list rename flows.",
            },
            "create_list": {
                "type": "boolean",
                "description": "Create the specified reminder list when action=list.",
                "default": False,
            },
            "clear_due": {
                "type": "boolean",
                "description": "Clear due date during edit.",
                "default": False,
            },
            "mark_complete": {
                "type": "boolean",
                "description": "Mark reminder complete during edit.",
                "default": False,
            },
            "mark_incomplete": {
                "type": "boolean",
                "description": "Mark reminder incomplete during edit.",
                "default": False,
            },
            "delete_list": {
                "type": "boolean",
                "description": "Delete the specified reminder list when action=list.",
                "default": False,
            },
            "force": {
                "type": "boolean",
                "description": "Use --force for delete, or --create for list create flows.",
                "default": False,
            },
            "output": {
                "type": "string",
                "enum": ["plain", "json", "quiet"],
                "description": "Output format for date-listing actions.",
                "default": "plain",
            },
            "verify": {
                "type": "boolean",
                "description": "After add, verify by listing the target day in plain output.",
                "default": True,
            },
        },
        "required": ["action"],
    },
}


registry.register(
    name="remindctl",
    toolset="terminal",
    schema=REMINDCTL_SCHEMA,
    handler=lambda args, **kw: remindctl_tool(
        action=args.get("action", ""),
        filter=args.get("filter", ""),
        title=args.get("title", ""),
        due=args.get("due", ""),
        time=args.get("time", ""),
        date=args.get("date", ""),
        list_name=args.get("list_name", ""),
        reminder_id=args.get("reminder_id", ""),
        reminder_ids=args.get("reminder_ids"),
        notes=args.get("notes", ""),
        priority=args.get("priority", ""),
        rename=args.get("rename", ""),
        create_list=bool(args.get("create_list", False)),
        clear_due=bool(args.get("clear_due", False)),
        mark_complete=bool(args.get("mark_complete", False)),
        mark_incomplete=bool(args.get("mark_incomplete", False)),
        delete_list=bool(args.get("delete_list", False)),
        force=bool(args.get("force", False)),
        output=args.get("output", "plain"),
        verify=bool(args.get("verify", True)),
    ),
    check_fn=check_remindctl_requirements,
    emoji="⏰",
)
