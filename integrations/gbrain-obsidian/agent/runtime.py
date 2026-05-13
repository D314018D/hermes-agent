from __future__ import annotations

import json
import os
import subprocess
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path

from core.input_normalizer import InputNormalizer
from core.schemas import HermesMessage
from routing.model_router import LOCAL_BASE_URL, route_model


PROJECT_ROOT = Path(__file__).resolve().parents[1]
QUEUE_PATH = PROJECT_ROOT / "logs" / "hermes-task-queue.jsonl"
RUN_LOG_PATH = PROJECT_ROOT / "logs" / "hermes-dispatch.jsonl"

SYSTEM_PROMPT = (
    "You are Hermes, an execution-first local agent. "
    "Choose the best next action for the user message. "
    "Return only JSON with keys summary, reply, actions. "
    "actions must be an array. Each action must include tool and optional payload. "
    "Allowed tools: run_ingest, enqueue_task, reply_only. "
    "Use run_ingest only for durable notes, vault, inbox, or explicit save/capture requests. "
    "Use enqueue_task for multi-step work that cannot be completed synchronously. "
    "Use reply_only when the user only needs an answer."
)


@dataclass
class ToolExecution:
    tool: str
    ok: bool
    payload: dict = field(default_factory=dict)
    result: dict = field(default_factory=dict)
    error: str = ""


@dataclass
class HermesDispatchResult:
    route: str
    model: str
    reply: str
    summary: str
    actions: list[ToolExecution]
    queue_path: str | None = None


class HermesAgentRuntime:
    def __init__(self) -> None:
        self.normalizer = InputNormalizer()

    def dispatch_payload(self, payload: dict) -> HermesDispatchResult:
        message = self.normalizer.normalize_payload(payload)
        return self.dispatch_message(message)

    def dispatch_message(self, message: HermesMessage) -> HermesDispatchResult:
        route = route_model(
            text=message.text,
            modality=message.input_type,
            attachments=message.attachments,
            wants_tts=False,
            has_voice_clone=False,
            force_router=True,
            log_decision=True,
            source=message.source,
            use_llm_router=True,
        )
        plan = self._build_plan(message, route)
        actions = [self._run_tool(message, item) for item in plan.get("actions", [])]
        reply = str(plan.get("reply") or "").strip() or self._default_reply(route.route, actions)
        summary = str(plan.get("summary") or "").strip() or route.reason
        result = HermesDispatchResult(
            route=route.route,
            model=route.model,
            reply=reply,
            summary=summary,
            actions=actions,
            queue_path=str(QUEUE_PATH) if any(item.tool == "enqueue_task" and item.ok for item in actions) else None,
        )
        self._log_run(message, result)
        return result

    def _build_plan(self, message: HermesMessage, route) -> dict:
        fallback = self._fallback_plan(message, route.route)
        plan = self._llm_plan(message, route.model, fallback)
        if not isinstance(plan, dict):
            return fallback
        actions = plan.get("actions")
        if not isinstance(actions, list):
            return fallback
        return {
            "summary": plan.get("summary") or fallback["summary"],
            "reply": plan.get("reply") or fallback["reply"],
            "actions": actions,
        }

    def _fallback_plan(self, message: HermesMessage, route_name: str) -> dict:
        if route_name == "tool_first_obsidian":
            return {
                "summary": "Store durable content in Obsidian through the ingestion pipeline.",
                "reply": "已收到，我会按规则写入 Obsidian。",
                "actions": [
                    {
                        "tool": "run_ingest",
                        "payload": {
                            "source_type": "text",
                            "source_app": f"{message.source}_agent",
                            "captured_at": message.timestamp,
                            "title": message.text[:72] or "Inbox Capture",
                            "content": message.text,
                            "attachments": message.attachments,
                            "metadata": message.metadata,
                        },
                    }
                ],
            }
        if route_name == "delegate_hermes_complex":
            return {
                "summary": "Queue complex work for asynchronous execution.",
                "reply": "任务已进入 Hermes 队列，我会按步骤继续执行。",
                "actions": [
                    {
                        "tool": "enqueue_task",
                        "payload": {
                            "title": message.text[:72] or "Queued Hermes Task",
                            "content": message.text,
                            "source": message.source,
                            "user_id": message.user_id,
                            "metadata": message.metadata,
                        },
                    }
                ],
            }
        return {
            "summary": "Reply directly without durable storage.",
            "reply": message.text,
            "actions": [{"tool": "reply_only", "payload": {"text": message.text}}],
        }

    def _llm_plan(self, message: HermesMessage, model: str, fallback: dict) -> dict | None:
        payload = {
            "model": model,
            "temperature": 0,
            "max_tokens": 400,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "text": message.text,
                            "source": message.source,
                            "source_type": message.source_type,
                            "input_type": message.input_type,
                            "timestamp": message.timestamp,
                            "attachments": message.attachments,
                            "metadata": message.metadata,
                            "fallback": fallback,
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
                **(
                    {"Authorization": f"Bearer {api_key}"}
                    if (api_key := (os.getenv("OMLX_API_KEY") or "").strip())
                    else {}
                ),
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            content = data["choices"][0]["message"]["content"]
            return self._extract_json(str(content))
        except (OSError, KeyError, IndexError, TypeError, ValueError, urllib.error.URLError):
            return None

    def _run_tool(self, message: HermesMessage, action: dict) -> ToolExecution:
        tool = str(action.get("tool") or "").strip()
        payload = action.get("payload") or {}
        if tool == "run_ingest":
            return self._run_ingest(payload, message)
        if tool == "enqueue_task":
            return self._enqueue_task(payload, message)
        if tool == "reply_only":
            return ToolExecution(tool=tool, ok=True, payload=payload, result={"reply": payload.get("text", "")})
        return ToolExecution(tool=tool or "unknown", ok=False, payload=payload, error="unsupported tool")

    def _run_ingest(self, payload: dict, message: HermesMessage) -> ToolExecution:
        merged = {
            "source_type": payload.get("source_type") or "text",
            "source_app": payload.get("source_app") or f"{message.source}_agent",
            "captured_at": payload.get("captured_at") or message.timestamp,
            "title": payload.get("title") or message.text[:72] or "Hermes Capture",
            "content": payload.get("content") or message.text,
            "attachments": payload.get("attachments") or message.attachments,
            "metadata": payload.get("metadata") or message.metadata,
        }
        cmd = ["python3", str(PROJECT_ROOT / "scripts" / "ingest.py"), "-"]
        try:
            env = dict(os.environ)
            env["STORE_LOW_VALUE_TO_INBOX"] = "true"
            completed = subprocess.run(
                cmd,
                input=json.dumps(merged, ensure_ascii=False),
                text=True,
                capture_output=True,
                cwd=PROJECT_ROOT,
                env=env,
                check=False,
            )
            result = json.loads(completed.stdout or "{}")
            return ToolExecution(
                tool="run_ingest",
                ok=completed.returncode == 0 and bool(result.get("should_store")),
                payload=merged,
                result=result,
                error=completed.stderr.strip(),
            )
        except (OSError, json.JSONDecodeError) as exc:
            return ToolExecution(tool="run_ingest", ok=False, payload=merged, error=str(exc))

    def _enqueue_task(self, payload: dict, message: HermesMessage) -> ToolExecution:
        record = {
            "title": payload.get("title") or message.text[:72] or "Hermes Task",
            "content": payload.get("content") or message.text,
            "source": payload.get("source") or message.source,
            "user_id": payload.get("user_id") or message.user_id,
            "timestamp": message.timestamp,
            "metadata": payload.get("metadata") or message.metadata,
            "status": "queued",
        }
        try:
            QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
            with QUEUE_PATH.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            return ToolExecution(tool="enqueue_task", ok=True, payload=payload, result=record)
        except OSError as exc:
            return ToolExecution(tool="enqueue_task", ok=False, payload=payload, error=str(exc))

    def _log_run(self, message: HermesMessage, result: HermesDispatchResult) -> None:
        record = {
            "message_id": message.message_id,
            "source": message.source,
            "source_type": message.source_type,
            "text": message.text,
            "route": result.route,
            "model": result.model,
            "summary": result.summary,
            "reply": result.reply,
            "actions": [asdict(item) for item in result.actions],
        }
        RUN_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with RUN_LOG_PATH.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    def _default_reply(self, route_name: str, actions: list[ToolExecution]) -> str:
        if any(item.tool == "run_ingest" and item.ok for item in actions):
            return "内容已交给 Obsidian ingestion。"
        if any(item.tool == "enqueue_task" and item.ok for item in actions):
            return "任务已进入 Hermes 队列。"
        if route_name == "direct_qwen":
            return "已收到。"
        return "已处理。"

    def _extract_json(self, text: str) -> dict | None:
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
