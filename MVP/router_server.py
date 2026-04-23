from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict

from common import json_response, post_json, read_json
from config import DEFAULT_TTS_MODEL, ROUTER_HOST, ROUTER_PORT, SUPERVISOR_HOST, SUPERVISOR_PORT


WEB_DIR = Path(__file__).parent / "web"


def apply_lightweight_rules(payload: Dict[str, Any]) -> Dict[str, Any]:
    source = payload.get("source", "gui")
    message = (payload.get("message") or "").strip()
    requested_capability = payload.get("capability") or "chat"
    wants_tts = bool(payload.get("tts"))

    normalized = {
        "source": source,
        "channel": source,
        "message": message,
        "tts": wants_tts,
        "capability": requested_capability,
        "model_hint": payload.get("model_hint", ""),
        "meta": payload.get("meta", {}),
    }

    if wants_tts:
        normalized["tts_model"] = DEFAULT_TTS_MODEL

    # Respect an explicit UI capability choice. Only infer when the caller
    # leaves the request in the default "chat" lane.
    if requested_capability == "chat":
        lower = message.lower()
        if any(keyword in lower for keyword in ("tool", "execute", "agent", "workflow", "schedule")):
            normalized["capability"] = "agent"
        elif any(keyword in lower for keyword in ("analyze", "reason", "plan", "compare")):
            normalized["capability"] = "reasoning"
    return normalized


class RouterHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self) -> None:
        json_response(self, {"ok": True})

    def do_GET(self) -> None:
        if self.path in ("/", "/index.html"):
            body = (WEB_DIR / "index.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path == "/health":
            json_response(
                self,
                {
                    "ok": True,
                    "service": "router",
                    "supervisor_url": f"http://{SUPERVISOR_HOST}:{SUPERVISOR_PORT}/v1/respond",
                },
            )
            return
        json_response(self, {"ok": False, "error": "Not found"}, status=404)

    def do_POST(self) -> None:
        if self.path != "/api/message":
            json_response(self, {"ok": False, "error": "Not found"}, status=404)
            return

        payload = read_json(self)
        if not payload.get("message"):
            json_response(self, {"ok": False, "error": "message is required"}, status=400)
            return

        routed = apply_lightweight_rules(payload)
        status, response = post_json(
            f"http://{SUPERVISOR_HOST}:{SUPERVISOR_PORT}/v1/respond",
            routed,
        )
        json_response(
            self,
            {
                "ok": status < 400 and response.get("ok", False),
                "routed_task": routed,
                "supervisor_response": response,
            },
            status=200 if status < 400 else status,
        )

    def log_message(self, format: str, *args) -> None:
        return


def main() -> None:
    server = ThreadingHTTPServer((ROUTER_HOST, ROUTER_PORT), RouterHandler)
    print(f"Router listening on http://{ROUTER_HOST}:{ROUTER_PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
