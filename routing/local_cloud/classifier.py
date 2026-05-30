"""Local/cloud route classifier.

This module only classifies turns and writes JSONL decision logs.  Execution
activation lives in ``routing.local_cloud.activation``.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

from hermes_constants import get_hermes_home
from routing.local_cloud.zh_rules import detect_zh_rule


LOCAL_TASKS = {
    "quick_chat",
    "memory",
    "routing",
    "reminders",
    "ingestion",
    "obsidian",
    "tools",
    "telegram",
}

CLOUD_TASKS = {
    "coding",
    "repo_refactor",
    "architecture",
    "debugging",
    "planning",
    "pr_review",
    "complex_reasoning",
}

HYBRID_TASKS = {
    "research_to_obsidian",
    "large_repo_question",
    "memory_based_planning",
}

TASK_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("pr_review", ("pr review", "pull request", "review this pr", "code review", "review diff")),
    ("repo_refactor", (
        "refactor",
        "restructure repo",
        "rename module",
        "split module",
        "large refactor",
        "review this repo",
        "review this repository",
        "review repo",
        "review repository",
        "modify the code",
        "change the code",
    )),
    ("debugging", ("debug", "traceback", "stack trace", "exception", "failing test", "fix bug", "why failing")),
    ("architecture", ("architecture", "design", "tradeoff", "scalability", "system design", "架构")),
    ("planning", ("plan", "roadmap", "implementation plan", "break down", "规划", "计划")),
    ("coding", ("write code", "implement", "patch", "modify file", "edit file", "add test", "编码", "代码")),
    ("obsidian", ("obsidian", "vault", "note", "frontmatter", "wikilink", "笔记")),
    ("memory", ("remember", "memory", "记住", "记忆")),
    ("reminders", ("remind", "reminder", "schedule", "提醒", "定时")),
    ("ingestion", ("ingest", "import", "transcribe", "parse document", "入库", "导入")),
    ("telegram", ("telegram", "tg ", "gateway", "网关")),
    ("tools", ("run command", "tool", "shell", "terminal", "执行命令")),
)

CODE_FILE_RE = re.compile(
    r"(^|\s)([\w./-]+\.(py|ts|tsx|js|jsx|go|rs|java|kt|swift|yaml|yml|toml|json|md|sh))(\s|$)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class RouteDecision:
    timestamp: str
    route: str
    task_type: str
    matched_rule: str
    confidence: float
    mode: str
    enabled: bool
    reasons: list[str] = field(default_factory=list)
    platform: str = ""
    session_id: str = ""
    session_key: str = ""
    message_chars: int = 0
    estimated_context_tokens: int = 0
    cloud_provider: str = ""
    cloud_model: str = ""


def classify_message(
    message: str,
    config: Mapping[str, Any] | None = None,
    *,
    platform: str = "",
    session_id: str = "",
    session_key: str = "",
    history: Sequence[Mapping[str, Any]] | None = None,
    context_prompt: str = "",
) -> RouteDecision:
    split_cfg = _split_config(config)
    enabled = bool(split_cfg.get("enabled", False))
    mode = str(split_cfg.get("mode") or "off")
    default_route = str(split_cfg.get("default_route") or "local")
    cloud_provider = str(split_cfg.get("cloud_provider") or "")
    cloud_model = str(split_cfg.get("cloud_model") or "")
    text = message or ""
    lower = text.lower()

    zh_match = detect_zh_rule(text, platform=platform, config=config)
    task_type, match_reason = _detect_task_type(lower, text)
    estimated_context_tokens = _estimate_context_tokens(text, history, context_prompt)
    reasons: list[str] = []
    matched_rule = match_reason
    if match_reason:
        reasons.append(match_reason)

    route = default_route
    confidence = 0.62 if task_type == "quick_chat" else 0.74

    if zh_match is not None:
        task_type = zh_match.task_type
        route = zh_match.route
        confidence = zh_match.confidence
        matched_rule = zh_match.matched_rule
        reasons.append(zh_match.reason)

    max_local = _as_int((_as_mapping(split_cfg.get("local_if"))).get("max_context_tokens"), 6000)
    min_cloud = _as_int((_as_mapping(split_cfg.get("cloud_if"))).get("min_context_tokens"), 6000)

    if zh_match is not None:
        if route == "cloud" and _looks_like_local_state_task(lower):
            route = "hybrid"
            confidence = max(confidence, 0.9)
            reasons.append("cloud_task_mentions_local_state")
    elif task_type in HYBRID_TASKS:
        route = "hybrid"
        confidence = 0.78
        reasons.append("task_type_is_hybrid")
    elif task_type in CLOUD_TASKS:
        route = "cloud"
        confidence = 0.82
        reasons.append("task_type_is_cloud_preferred")
    elif estimated_context_tokens >= min_cloud:
        route = "cloud"
        confidence = 0.76
        reasons.append(f"estimated_context_tokens>={min_cloud}")
    elif task_type in LOCAL_TASKS:
        route = "local"
        confidence = 0.84
        reasons.append("task_type_is_local")
    elif estimated_context_tokens <= max_local:
        route = "local"
        confidence = 0.60
        reasons.append(f"estimated_context_tokens<={max_local}")

    if zh_match is None and route == "cloud" and _looks_like_local_state_task(lower):
        route = "hybrid"
        confidence = max(confidence, 0.78)
        reasons.append("cloud_task_mentions_local_state")

    ask_below = _as_float(split_cfg.get("ask_when_confidence_below"), 0.55)
    if confidence < ask_below:
        route = "ask"
        reasons.append(f"confidence_below_{ask_below:g}")

    return RouteDecision(
        timestamp=datetime.now(timezone.utc).isoformat(),
        route=route,
        task_type=task_type,
        matched_rule=matched_rule,
        confidence=round(confidence, 2),
        mode=mode,
        enabled=enabled,
        reasons=reasons,
        platform=platform,
        session_id=session_id,
        session_key=session_key,
        message_chars=len(text),
        estimated_context_tokens=estimated_context_tokens,
        cloud_provider=cloud_provider,
        cloud_model=cloud_model,
    )


def write_route_decision(
    decision: RouteDecision,
    config: Mapping[str, Any] | None = None,
    *,
    hermes_home: Path | None = None,
) -> Path | None:
    split_cfg = _split_config(config)
    logging_cfg = _as_mapping(split_cfg.get("logging"))
    if not bool(logging_cfg.get("enabled", False)):
        return None

    raw_path = str(logging_cfg.get("path") or "logs/local-cloud-routing.jsonl")
    base = hermes_home or get_hermes_home()
    log_path = Path(raw_path)
    if not log_path.is_absolute():
        log_path = base / log_path
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(asdict(decision), ensure_ascii=False, sort_keys=True) + "\n")
    return log_path


def _split_config(config: Mapping[str, Any] | None) -> Mapping[str, Any]:
    if not isinstance(config, Mapping):
        return {}
    agent = config.get("agent")
    if isinstance(agent, Mapping):
        split = agent.get("local_cloud_split")
        if isinstance(split, Mapping):
            return split
    return {}


def _detect_task_type(lower: str, original: str) -> tuple[str, str]:
    for task_type, needles in TASK_PATTERNS:
        if any(needle in lower for needle in needles):
            return task_type, f"matched_{task_type}_keyword"
    if CODE_FILE_RE.search(original):
        return "coding", "matched_code_file_reference"
    if "?" in original or "？" in original:
        return "quick_chat", "default_question"
    return "quick_chat", "default_short_chat"


def _estimate_context_tokens(
    message: str,
    history: Sequence[Mapping[str, Any]] | None,
    context_prompt: str,
) -> int:
    chars = len(message or "") + len(context_prompt or "")
    for msg in history or []:
        if not isinstance(msg, Mapping):
            continue
        chars += len(str(msg.get("content") or ""))
    return max(1, chars // 4)


def _looks_like_local_state_task(lower: str) -> bool:
    return any(
        term in lower
        for term in (
            "obsidian",
            "memory",
            "remember",
            "vault",
            "telegram",
            "wechat",
            "gbrain",
            "记忆",
            "笔记",
            "微信",
        )
    )


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _as_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
