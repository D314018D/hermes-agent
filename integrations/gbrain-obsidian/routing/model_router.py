from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ROUTING_LOG = PROJECT_ROOT / "logs" / "model-routing.jsonl"
ROUTING_NOTE = PROJECT_ROOT / "obsidian-vault" / "06-skills" / "current-model-routing.md"

DIRECT_QWEN_ROUTE = "direct_qwen"
TOOL_FIRST_OBSIDIAN_ROUTE = "tool_first_obsidian"
DELEGATE_HERMES_ROUTE = "delegate_hermes_complex"
VISION_QWEN_ROUTE = "vision_qwen_vl"
TTS_QWEN_ROUTE = "tts_qwen"

QWEN_BRAIN_MODEL = "Qwen2.5-7B-Instruct-4bit"
HERMES_AGENT_MODEL = "Hermes-3-Llama-3.1-8B-4bit"
QWEN_VISION_MODEL = "Qwen3-VL-4B-Instruct-MLX-4bit"
QWEN_TTS_MODEL = "Qwen3-TTS-12Hz-0.6B-CustomVoice-8bit"
LOCAL_PROVIDER = "custom"
LOCAL_BASE_URL = "http://127.0.0.1:8000/v1"

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".heic", ".heif"}
OBSIDIAN_WORDS = (
    "obsidian", "obisdian", "vault", "inbox", "note", "notes",
    "保存", "存入", "写入", "记录", "记入", "收件箱", "笔记", "知识库",
)
WRITE_WORDS = (
    "save", "store", "capture", "write", "record", "put", "add",
    "保存", "存入", "写入", "记录", "记入", "放入", "加入",
)
COMPLEX_WORDS = (
    "architecture", "refactor", "debug", "investigate", "analyze", "review",
    "multi-step", "complex", "plan", "implement", "research", "reason",
    "架构", "重构", "调试", "排查", "分析", "复杂", "实现", "研究", "推理",
)
TTS_WORDS = ("tts", "speak", "read aloud", "voice", "朗读", "语音", "念出来", "配音")
VISION_WORDS = ("image", "photo", "screenshot", "vision", "图片", "照片", "截图", "看图")


@dataclass(frozen=True)
class ModelRoute:
    route: str
    model: str
    router_model: str = QWEN_BRAIN_MODEL
    provider: str = LOCAL_PROVIDER
    base_url: str = LOCAL_BASE_URL
    reason: str = ""
    confidence: float = 1.0
    tool_action: str = ""
    tool_entrypoint: str = ""
    metadata: dict = field(default_factory=dict)


def route_model(
    text: str = "",
    modality: str = "text",
    attachments: list[str] | None = None,
    wants_tts: bool = False,
    has_voice_clone: bool = False,
    force_router: bool = False,
    log_decision: bool = False,
    source: str = "manual",
    use_llm_router: bool = False,
    llm_timeout: float = 8.0,
) -> ModelRoute:
    attachments = attachments or []
    normalized_text = " ".join(str(text or "").lower().split())
    normalized_modality = str(modality or "text").lower()
    has_image = _has_image_input(normalized_text, normalized_modality, attachments)
    wants_audio = bool(wants_tts) or any(word in normalized_text for word in TTS_WORDS)
    wants_obsidian_write = _wants_obsidian_write(normalized_text)
    is_complex = _is_complex_request(normalized_text)

    if wants_obsidian_write:
        route = ModelRoute(
            route=TOOL_FIRST_OBSIDIAN_ROUTE,
            model=QWEN_BRAIN_MODEL,
            reason="Qwen detected durable Obsidian capture intent; use the ingestion pipeline before freeform file writes.",
            confidence=0.94,
            tool_action="run_ingest",
            tool_entrypoint="python3 scripts/ingest.py -",
            metadata={
                "selected_by": "qwen_brain_router",
                "forced_router": bool(force_router),
                "should_call_tool": True,
                "tool": "ingestion_pipeline",
                "target_hint": "obsidian-vault/00-inbox or resolver-selected page",
                "switch_main_model": False,
            },
        )
    elif has_image:
        route = ModelRoute(
            route=VISION_QWEN_ROUTE,
            model=QWEN_VISION_MODEL,
            reason="Qwen detected visual input; route to the local Qwen vision model.",
            confidence=0.9,
            metadata={
                "selected_by": "qwen_brain_router",
                "forced_router": bool(force_router),
                "should_call_tool": False,
                "switch_main_model": True,
                "modality": "vision",
            },
        )
    elif wants_audio:
        route = ModelRoute(
            route=TTS_QWEN_ROUTE,
            model=QWEN_TTS_MODEL,
            reason="Qwen detected a speech/TTS request; route output generation to the local Qwen TTS model.",
            confidence=0.88,
            metadata={
                "selected_by": "qwen_brain_router",
                "forced_router": bool(force_router),
                "should_call_tool": True,
                "tool": "tts",
                "switch_main_model": False,
                "has_voice_clone": bool(has_voice_clone),
            },
        )
    elif is_complex:
        route = ModelRoute(
            route=DELEGATE_HERMES_ROUTE,
            model=HERMES_AGENT_MODEL,
            reason="Qwen marked the request as complex enough to delegate to Hermes for deeper multi-step reasoning.",
            confidence=0.82,
            metadata={
                "selected_by": "qwen_brain_router",
                "forced_router": bool(force_router),
                "should_call_tool": False,
                "switch_main_model": True,
                "complexity": "high",
            },
        )
    else:
        route = ModelRoute(
            route=DIRECT_QWEN_ROUTE,
            model=QWEN_BRAIN_MODEL,
            reason="Qwen can answer directly without model escalation.",
            confidence=0.78,
            metadata={
                "selected_by": "qwen_brain_router",
                "forced_router": bool(force_router),
                "should_call_tool": False,
                "switch_main_model": False,
                "complexity": "normal",
            },
        )

    if use_llm_router:
        llm_choice = _qwen_router_choice(
            text=text,
            modality=modality,
            attachments=attachments,
            wants_tts=wants_tts,
            has_voice_clone=has_voice_clone,
            force_router=force_router,
            rule_suggestion=route.route,
            timeout=llm_timeout,
        )
        if llm_choice and llm_choice.get("route") in {
            DIRECT_QWEN_ROUTE,
            TOOL_FIRST_OBSIDIAN_ROUTE,
            DELEGATE_HERMES_ROUTE,
            VISION_QWEN_ROUTE,
            TTS_QWEN_ROUTE,
        }:
            route = _route_from_name(
                str(llm_choice["route"]),
                force_router=force_router,
                has_voice_clone=has_voice_clone,
                reason_override=str(llm_choice.get("reason") or ""),
                confidence_override=_coerce_confidence(llm_choice.get("confidence")),
            )
            route = _with_metadata(route, {
                "llm_router_used": True,
                "rule_suggestion": llm_choice.get("rule_suggestion") or route.route,
            })
        else:
            route = _with_metadata(route, {"llm_router_used": False})

    if log_decision:
        record_route_decision(route, text=text, attachments=attachments, source=source)
    return route


def record_route_decision(
    route: ModelRoute,
    text: str = "",
    attachments: list[str] | None = None,
    source: str = "manual",
) -> None:
    timestamp = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    event = {
        "timestamp": timestamp,
        "source": source,
        "text_preview": " ".join(str(text or "").split())[:240],
        "attachments": list(attachments or []),
        "decision": asdict(route),
    }
    try:
        ROUTING_LOG.parent.mkdir(parents=True, exist_ok=True)
        with ROUTING_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
        if ROUTING_NOTE.exists():
            with ROUTING_NOTE.open("a", encoding="utf-8") as f:
                f.write(
                    "\n"
                    f"### {timestamp} - {source}/router\n\n"
                    f"- Router model: {route.router_model}\n"
                    f"- Selected route: {route.route}\n"
                    f"- Selected model: {route.model}\n"
                    f"- Tool action: {route.tool_action or 'none'}\n"
                    f"- Reason: {route.reason}\n"
                )
    except OSError:
        # Routing must never fail just because observability storage is unavailable.
        return


def _wants_obsidian_write(text: str) -> bool:
    return any(word in text for word in OBSIDIAN_WORDS) and any(word in text for word in WRITE_WORDS)


def _has_image_input(text: str, modality: str, attachments: list[str]) -> bool:
    if modality in {"image", "vision", "photo", "screenshot"}:
        return True
    if any(word in text for word in VISION_WORDS):
        return True
    for item in attachments:
        suffix = Path(str(item)).suffix.lower()
        if suffix in IMAGE_EXTS:
            return True
    return False


def _is_complex_request(text: str) -> bool:
    if len(text) > 1200:
        return True
    return any(word in text for word in COMPLEX_WORDS)


def _qwen_router_choice(
    text: str,
    modality: str,
    attachments: list[str],
    wants_tts: bool,
    has_voice_clone: bool,
    force_router: bool,
    rule_suggestion: str,
    timeout: float,
) -> dict | None:
    payload = {
        "model": QWEN_BRAIN_MODEL,
        "temperature": 0,
        "max_tokens": 220,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are the Qwen first-pass brain for Hermes. Choose exactly one route "
                    "from: direct_qwen, tool_first_obsidian, delegate_hermes_complex, "
                    "vision_qwen_vl, tts_qwen. Return only JSON with keys route, reason, "
                    "confidence. Use tool_first_obsidian when the user wants durable Obsidian, "
                    "vault, or inbox capture. Use delegate_hermes_complex for complex multi-step "
                    "reasoning or implementation. Use vision_qwen_vl for image inputs. Use "
                    "tts_qwen for speech output. Otherwise use direct_qwen."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "text": str(text or "")[:4000],
                        "modality": modality,
                        "attachments": attachments,
                        "wants_tts": wants_tts,
                        "has_voice_clone": has_voice_clone,
                        "force_router": force_router,
                        "rule_suggestion": rule_suggestion,
                    },
                    ensure_ascii=False,
                ),
            },
        ],
    }
    req = urllib.request.Request(
        f"{LOCAL_BASE_URL.rstrip('/')}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {_router_api_key()}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=max(0.5, float(timeout))) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"]
        return _extract_json_object(str(content))
    except (OSError, KeyError, IndexError, TypeError, ValueError, urllib.error.URLError):
        return None


def _extract_json_object(text: str) -> dict | None:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped.lower().startswith("json"):
            stripped = stripped[4:].strip()
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start < 0 or end < start:
        return None
    try:
        obj = json.loads(stripped[start : end + 1])
        return obj if isinstance(obj, dict) else None
    except json.JSONDecodeError:
        return None


def _route_from_name(
    route_name: str,
    force_router: bool,
    has_voice_clone: bool,
    reason_override: str = "",
    confidence_override: float | None = None,
) -> ModelRoute:
    if route_name == TOOL_FIRST_OBSIDIAN_ROUTE:
        return ModelRoute(
            route=TOOL_FIRST_OBSIDIAN_ROUTE,
            model=QWEN_BRAIN_MODEL,
            reason=reason_override or "Qwen selected durable Obsidian capture via the ingestion pipeline.",
            confidence=confidence_override or 0.9,
            tool_action="run_ingest",
            tool_entrypoint="python3 scripts/ingest.py -",
            metadata={
                "selected_by": "qwen_brain_router",
                "forced_router": bool(force_router),
                "should_call_tool": True,
                "tool": "ingestion_pipeline",
                "target_hint": "obsidian-vault/00-inbox or resolver-selected page",
                "switch_main_model": False,
            },
        )
    if route_name == VISION_QWEN_ROUTE:
        return ModelRoute(
            route=VISION_QWEN_ROUTE,
            model=QWEN_VISION_MODEL,
            reason=reason_override or "Qwen selected the local vision model for visual input.",
            confidence=confidence_override or 0.86,
            metadata={
                "selected_by": "qwen_brain_router",
                "forced_router": bool(force_router),
                "should_call_tool": False,
                "switch_main_model": True,
                "modality": "vision",
            },
        )
    if route_name == TTS_QWEN_ROUTE:
        return ModelRoute(
            route=TTS_QWEN_ROUTE,
            model=QWEN_TTS_MODEL,
            reason=reason_override or "Qwen selected the local TTS model for speech output.",
            confidence=confidence_override or 0.86,
            metadata={
                "selected_by": "qwen_brain_router",
                "forced_router": bool(force_router),
                "should_call_tool": True,
                "tool": "tts",
                "switch_main_model": False,
                "has_voice_clone": bool(has_voice_clone),
            },
        )
    if route_name == DELEGATE_HERMES_ROUTE:
        return ModelRoute(
            route=DELEGATE_HERMES_ROUTE,
            model=HERMES_AGENT_MODEL,
            reason=reason_override or "Qwen selected Hermes for deeper multi-step reasoning.",
            confidence=confidence_override or 0.8,
            metadata={
                "selected_by": "qwen_brain_router",
                "forced_router": bool(force_router),
                "should_call_tool": False,
                "switch_main_model": True,
                "complexity": "high",
            },
        )
    return ModelRoute(
        route=DIRECT_QWEN_ROUTE,
        model=QWEN_BRAIN_MODEL,
        reason=reason_override or "Qwen selected direct handling without escalation.",
        confidence=confidence_override or 0.75,
        metadata={
            "selected_by": "qwen_brain_router",
            "forced_router": bool(force_router),
            "should_call_tool": False,
            "switch_main_model": False,
            "complexity": "normal",
        },
    )


def _with_metadata(route: ModelRoute, updates: dict) -> ModelRoute:
    metadata = dict(route.metadata)
    metadata.update(updates)
    return replace(route, metadata=metadata)


def _coerce_confidence(value) -> float | None:
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return None
    return max(0.0, min(1.0, confidence))


def _router_api_key() -> str:
    return os.getenv("QWEN_ROUTER_API_KEY") or os.getenv("OMLX_API_KEY") or ""
