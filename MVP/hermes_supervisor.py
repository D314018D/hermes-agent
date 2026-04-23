from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List

from common import json_response, now_iso, post_json, read_json
from config import (
    DEFAULT_AGENT_MODEL,
    DEFAULT_CHAT_MODEL,
    DEFAULT_REASONING_MODEL,
    OMLX_API_KEY,
    OMLX_BASE_URL,
    OMLX_MOCK,
    SUPERVISOR_HOST,
    SUPERVISOR_PORT,
)


def choose_model(task: Dict[str, Any]) -> str:
    model_hint = (task.get("model_hint") or "").strip()
    capability = (task.get("capability") or "chat").strip()

    if model_hint:
        return model_hint
    if capability == "reasoning":
        return DEFAULT_REASONING_MODEL
    if capability == "agent":
        return DEFAULT_AGENT_MODEL
    return DEFAULT_CHAT_MODEL


def build_messages(task: Dict[str, Any]) -> List[Dict[str, str]]:
    system_prompt = (
        "You are the local Hermes supervisor execution model. "
        "Be concise, reliable, and tool-friendly."
    )
    context = (
        f"source={task.get('source', 'gui')}; "
        f"channel={task.get('channel', 'chat')}; "
        f"tts={bool(task.get('tts'))}"
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "system", "content": context},
        {"role": "user", "content": task.get("message", "")},
    ]


def mock_reply(task: Dict[str, Any], model: str) -> Dict[str, Any]:
    return {
        "ok": True,
        "mode": "mock",
        "model": model,
        "reply": f"[mock:{model}] Hermes received: {task.get('message', '')}",
        "timestamp": now_iso(),
    }


def call_omlx(task: Dict[str, Any]) -> Dict[str, Any]:
    model = choose_model(task)
    if OMLX_MOCK:
        return mock_reply(task, model)

    payload = {
        "model": model,
        "messages": build_messages(task),
        "temperature": 0.3,
    }
    headers = {}
    if OMLX_API_KEY:
        headers["Authorization"] = f"Bearer {OMLX_API_KEY}"

    status, data = post_json(f"{OMLX_BASE_URL}/chat/completions", payload, headers=headers)
    if status >= 400:
        return {
            "ok": False,
            "mode": "live",
            "model": model,
            "error": data.get("error", "Unknown upstream error"),
            "timestamp": now_iso(),
        }

    choice = ((data.get("choices") or [{}])[0]).get("message", {})
    return {
        "ok": True,
        "mode": "live",
        "model": model,
        "reply": choice.get("content", ""),
        "raw": data,
        "timestamp": now_iso(),
    }


class SupervisorHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self) -> None:
        json_response(self, {"ok": True})

    def do_GET(self) -> None:
        if self.path == "/health":
            json_response(
                self,
                {
                    "ok": True,
                    "service": "hermes-supervisor",
                    "omlx_base_url": OMLX_BASE_URL,
                    "mock": OMLX_MOCK,
                    "routing": {
                        "chat": DEFAULT_CHAT_MODEL,
                        "reasoning": DEFAULT_REASONING_MODEL,
                        "agent": DEFAULT_AGENT_MODEL,
                    },
                },
            )
            return
        json_response(self, {"ok": False, "error": "Not found"}, status=404)

    def do_POST(self) -> None:
        if self.path != "/v1/respond":
            json_response(self, {"ok": False, "error": "Not found"}, status=404)
            return

        task = read_json(self)
        if not task.get("message"):
            json_response(self, {"ok": False, "error": "message is required"}, status=400)
            return
        json_response(self, call_omlx(task))

    def log_message(self, format: str, *args) -> None:
        return


def main() -> None:
    server = ThreadingHTTPServer((SUPERVISOR_HOST, SUPERVISOR_PORT), SupervisorHandler)
    print(f"Hermes Supervisor listening on http://{SUPERVISOR_HOST}:{SUPERVISOR_PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
