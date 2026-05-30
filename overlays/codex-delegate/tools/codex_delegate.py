#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "logs"

STATUSES = {
    "ok",
    "failed",
    "blocked_secret",
    "blocked_private_cloud",
    "need_api_approval",
    "need_manual_codex_intervention",
    "timeout",
    "quota_exhausted_private_no_fallback",
}

SECRET_PATTERN = re.compile(
    r"\b(password|api[_ -]?key|secret[_ -]?key|private[_ -]?key|recovery[_ -]?code|token|credential)\b",
    re.IGNORECASE,
)

QUOTA_PATTERN = re.compile(
    r"(rate limit|quota|usage limit|credits|too many requests|insufficient_quota|billing)",
    re.IGNORECASE,
)

CODEX_SCOPE_PATTERN = re.compile(
    r"\b("
    r"code|coding|debug|debugging|refactor|repository|repo|multi-file|implementation|"
    r"script|automation|test|tests|pytest|build|ci|python|javascript|typescript|"
    r"power bi|power query|sql|review|diff|patch|bug|runtime|compile"
    r")\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ContextPack:
    task_id: str
    task_hash: str
    user_goal: str
    privacy_level: str
    route_reason: str
    recent_context_summary: str
    relevant_memory_summary: str
    allowed_working_directory: str
    allowed_read_paths: list[str]
    allowed_write_paths: list[str]
    forbidden_paths: list[str]
    network_policy: str
    api_fallback_allowed: bool
    api_fallback_approved: bool
    output_required: list[str]
    timeout_seconds: int
    max_output_chars: int
    codex_profile: str
    dry_run: bool
    simulate_codex_output: str | None

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "ContextPack":
        user_goal = str(data.get("user_goal") or "").strip()
        task_hash = str(data.get("task_hash") or "").strip() or _hash_text(user_goal)
        task_id = str(data.get("task_id") or task_hash[:16]).strip()
        privacy_level = str(data.get("privacy_level") or "private").strip().lower()
        network_policy = str(data.get("network_policy") or "disabled").strip().lower()
        timeout_seconds = int(data.get("timeout_seconds") or 600)
        max_output_chars = int(data.get("max_output_chars") or 60000)
        return cls(
            task_id=task_id,
            task_hash=task_hash,
            user_goal=user_goal,
            privacy_level=privacy_level,
            route_reason=str(data.get("route_reason") or "").strip(),
            recent_context_summary=str(data.get("recent_context_summary") or "").strip(),
            relevant_memory_summary=str(data.get("relevant_memory_summary") or "").strip(),
            allowed_working_directory=str(data.get("allowed_working_directory") or str(ROOT)).strip(),
            allowed_read_paths=_string_list(data.get("allowed_read_paths")),
            allowed_write_paths=_string_list(data.get("allowed_write_paths")),
            forbidden_paths=_string_list(data.get("forbidden_paths")),
            network_policy=network_policy,
            api_fallback_allowed=bool(data.get("api_fallback_allowed", False)),
            api_fallback_approved=bool(data.get("api_fallback_approved", False)),
            output_required=_string_list(
                data.get("output_required")
                or ["final_answer", "task_summary", "memory_candidate", "skill_candidate"]
            ),
            timeout_seconds=max(1, min(timeout_seconds, 3600)),
            max_output_chars=max(1000, min(max_output_chars, 250000)),
            codex_profile=str(data.get("codex_profile") or "codex-delegate").strip(),
            dry_run=bool(data.get("dry_run", False)),
            simulate_codex_output=(
                str(data["simulate_codex_output"])
                if data.get("simulate_codex_output") is not None
                else None
            ),
        )


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def _hash_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _is_secret(context: ContextPack) -> bool:
    combined = "\n".join(
        [
            context.user_goal,
            context.route_reason,
            context.recent_context_summary,
            context.relevant_memory_summary,
        ]
    )
    return context.privacy_level == "secret" or bool(SECRET_PATTERN.search(combined))


def _is_codex_scope(context: ContextPack) -> bool:
    combined = f"{context.user_goal}\n{context.route_reason}"
    return bool(CODEX_SCOPE_PATTERN.search(combined))


def _is_cloud_route(context: ContextPack) -> bool:
    profile = context.codex_profile.lower()
    return any(marker in profile for marker in ["chatgpt", "api", "paid", "openai"])


def build_child_env(api_fallback_approved: bool) -> dict[str, str]:
    env = dict(os.environ)
    if not api_fallback_approved:
        for key in list(env):
            if key.upper() in {"OPENAI_API_KEY", "OPENAI_KEY"}:
                env.pop(key, None)
    return env


def classify_codex_output(context: ContextPack, output: str) -> str:
    if not QUOTA_PATTERN.search(output):
        return "ok"
    if context.privacy_level == "private":
        return "quota_exhausted_private_no_fallback"
    if context.privacy_level == "secret":
        return "blocked_secret"
    if context.api_fallback_allowed and context.api_fallback_approved:
        return "ok"
    return "need_api_approval"


def _base_response(context: ContextPack, status: str, error: str | None = None) -> dict[str, Any]:
    if status not in STATUSES:
        raise ValueError(f"unsupported status: {status}")
    review_date = (datetime.now(timezone.utc).date() + timedelta(days=30)).isoformat()
    return {
        "status": status,
        "ok": status == "ok",
        "task_id": context.task_id,
        "task_hash": context.task_hash,
        "error": error,
        "final_answer": "",
        "task_summary": {
            "user_goal": "redacted: held by Hermes context pack",
            "route_used": "codex_delegate",
            "provider_used": context.codex_profile,
            "files_read": [],
            "files_changed": [],
            "commands_executed": [],
            "key_decisions": [
                "Hermes remains router and memory owner",
                "Codex result is candidate material only",
            ],
            "errors": [error] if error else [],
            "follow_up_actions": [],
        },
        "memory_candidate": {
            "should_store": "no",
            "memory_type": "none",
            "confidence": "low",
            "suggested_gbrain_ingest": "no",
            "suggested_obsidian_persistence": "no",
            "suggested_note_title": "",
            "suggested_memory_text": "",
            "expiry_or_review_date": review_date,
            "do_not_store": "raw private content, secrets, credentials, API keys",
        },
        "skill_candidate": {
            "should_create_or_update_skill": "no",
            "skill_id": "",
            "existing_skill_matched": "",
            "proposed_change": "",
            "reason": "",
            "risk": "low",
        },
    }


def _prompt_for_codex(context: ContextPack) -> str:
    return "\n".join(
        [
            "You are a delegated executor called by Hermes.",
            "Hermes remains the router, memory owner, and skills owner.",
            "Return final answer plus Task Summary, Memory Candidate, and Skill Candidate.",
            "",
            f"Task ID: {context.task_id}",
            f"Privacy: {context.privacy_level}",
            f"Route reason: {context.route_reason}",
            f"Goal: {context.user_goal}",
            "",
            "Do not store or expose secrets. Do not write to GBrain, Obsidian canonical notes, or Hermes skills.",
        ]
    )


def _run_codex(context: ContextPack) -> tuple[str, str | None]:
    if context.simulate_codex_output is not None:
        return context.simulate_codex_output, None
    if context.dry_run:
        return "Dry run: Codex invocation skipped.", None

    workdir = Path(context.allowed_working_directory).expanduser().resolve()
    if not workdir.exists() or not workdir.is_dir():
        return "", f"allowed_working_directory does not exist: {workdir}"

    command = ["codex", "--profile", context.codex_profile, "exec", _prompt_for_codex(context)]
    try:
        completed = subprocess.run(
            command,
            cwd=str(workdir),
            env=build_child_env(context.api_fallback_approved),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=context.timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return "", "timeout"
    except FileNotFoundError:
        return "", "codex command not found"

    output = (completed.stdout or "") + (completed.stderr or "")
    if completed.returncode != 0 and not QUOTA_PATTERN.search(output):
        return output[: context.max_output_chars], f"codex exited with {completed.returncode}"
    return output[: context.max_output_chars], None


def _audit(context: ContextPack, status: str, files_changed: list[str] | None = None) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    event = {
        "timestamp": _now(),
        "task_hash": context.task_hash,
        "privacy_level": context.privacy_level,
        "route": "codex_delegate",
        "api_fallback_requested": status == "need_api_approval",
        "api_fallback_approved": context.api_fallback_approved,
        "files_changed": files_changed or [],
        "memory_candidate_generated": True,
        "status": status,
    }
    with (LOG_DIR / "codex_delegate.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def delegate(context: ContextPack) -> dict[str, Any]:
    if context.privacy_level not in {"public", "private", "secret"}:
        response = _base_response(context, "failed", "privacy_level must be public, private, or secret")
        _audit(context, response["status"])
        return response
    if not context.user_goal:
        response = _base_response(context, "failed", "user_goal is required")
        _audit(context, response["status"])
        return response
    if _is_secret(context):
        response = _base_response(context, "blocked_secret", "secret material must not be delegated")
        _audit(context, response["status"])
        return response
    if context.privacy_level == "private" and (context.api_fallback_approved or _is_cloud_route(context)):
        response = _base_response(context, "blocked_private_cloud", "private tasks cannot use cloud/API fallback")
        _audit(context, response["status"])
        return response
    if not _is_codex_scope(context):
        response = _base_response(context, "failed", "task is outside Codex delegate scope")
        _audit(context, response["status"])
        return response

    output, error = _run_codex(context)
    if error == "timeout":
        response = _base_response(context, "timeout", "Codex invocation timed out")
        _audit(context, response["status"])
        return response
    if error:
        response = _base_response(context, "failed", error)
        response["final_answer"] = output
        _audit(context, response["status"])
        return response

    status = classify_codex_output(context, output)
    response = _base_response(context, status)
    response["final_answer"] = output
    if status == "need_api_approval":
        response["task_summary"]["follow_up_actions"].append(
            "Codex ChatGPT quota appears exhausted. Ask Hermes for one-time API fallback approval for this non-private task only."
        )
    if status == "quota_exhausted_private_no_fallback":
        response["task_summary"]["errors"].append("Quota exhausted and private task cannot use cloud/API fallback.")
    _audit(context, response["status"])
    return response


def load_context(path: str | None) -> ContextPack:
    raw = sys.stdin.read() if path in {None, "-"} else Path(path).read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("context pack must be a JSON object")
    return ContextPack.from_mapping(data)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Hermes guarded Codex delegate wrapper")
    parser.add_argument("--context", "-c", default="-", help="JSON Context Pack path, or '-' for stdin")
    parser.add_argument("--dry-run", action="store_true", help="Skip Codex invocation")
    args = parser.parse_args(argv)

    try:
        context = load_context(args.context)
        if args.dry_run:
            context = ContextPack.from_mapping({**context.__dict__, "dry_run": True})
        response = delegate(context)
    except Exception as exc:
        fallback_context = ContextPack.from_mapping({"user_goal": "", "privacy_level": "private"})
        response = _base_response(fallback_context, "failed", str(exc))
    print(json.dumps(response, ensure_ascii=False, indent=2))
    return 0 if response.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
