import os
from pathlib import Path


def load_env(path: str = ".env") -> None:
    env_path = Path(path)
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


load_env()


ROUTER_HOST = os.getenv("ROUTER_HOST", "127.0.0.1")
ROUTER_PORT = int(os.getenv("ROUTER_PORT", "8080"))
SUPERVISOR_HOST = os.getenv("SUPERVISOR_HOST", "127.0.0.1")
SUPERVISOR_PORT = int(os.getenv("SUPERVISOR_PORT", "8090"))

OMLX_BASE_URL = os.getenv("OMLX_BASE_URL", "http://127.0.0.1:11434/v1").rstrip("/")
OMLX_API_KEY = os.getenv("OMLX_API_KEY", "")
OMLX_MOCK = os.getenv("OMLX_MOCK", "true").lower() == "true"

DEFAULT_CHAT_MODEL = os.getenv("DEFAULT_CHAT_MODEL", "qwen2.5")
DEFAULT_REASONING_MODEL = os.getenv("DEFAULT_REASONING_MODEL", "qwen3.5")
DEFAULT_AGENT_MODEL = os.getenv("DEFAULT_AGENT_MODEL", "Hermes-2-Pro")
DEFAULT_TTS_MODEL = os.getenv("DEFAULT_TTS_MODEL", "qwen3-tts")
