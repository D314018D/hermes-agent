import http.client
import json
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Optional, Tuple


def json_response(handler, payload: Dict[str, Any], status: int = 200) -> None:
    body = json.dumps(payload, ensure_ascii=True).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.end_headers()
    handler.wfile.write(body)


def read_json(handler) -> Dict[str, Any]:
    content_length = int(handler.headers.get("Content-Length", "0"))
    raw = handler.rfile.read(content_length) if content_length else b"{}"
    return json.loads(raw.decode("utf-8") or "{}")


def post_json(url: str, payload: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> Tuple[int, Dict[str, Any]]:
    request_headers = {"Content-Type": "application/json"}
    if headers:
        request_headers.update(headers)

    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=request_headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            try:
                body = response.read().decode("utf-8")
            except http.client.IncompleteRead as exc:
                partial = exc.partial.decode("utf-8", errors="replace")
                try:
                    return response.status, json.loads(partial)
                except json.JSONDecodeError:
                    return 502, {"error": "Upstream returned an incomplete response"}
            return response.status, json.loads(body)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return exc.code, {"error": body}
    except urllib.error.URLError as exc:
        return 502, {"error": f"Upstream unavailable: {exc.reason}"}
    except http.client.RemoteDisconnected:
        return 502, {"error": "Upstream closed the connection unexpectedly"}


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
