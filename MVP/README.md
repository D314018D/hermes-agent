# Hermes Agent Minimal Local Stack

This is a minimal runnable prototype for the flow:

`GUI -> Lightweight Router -> Hermes Supervisor -> oMLX -> Local Models`

For external channels such as Weixin (WeChat), WeCom, and Email, use Hermes Agent's native messaging gateway instead of building custom adapters inside this MVP.

It includes:

- a lightweight router service
- a Hermes-style supervisor service
- a small browser GUI for testing the flow
- environment-based model routing
- a clean boundary between MVP browser testing and Hermes-native external integrations

## Model Routing

This MVP uses a fixed three-lane model policy:

- `chat` -> `Qwen2.5-7B-Instruct-4bit`
- `reasoning` -> `Qwen3.5-9B-MLX-4bit`
- `agent` -> `Hermes-2-Pro-Mistral-7B-4bit`

Notes:

- explicit `model_hint` always wins
- explicit UI capability selection wins over keyword inference
- keyword inference only runs when the request stays in the default `chat` lane

## Architecture

- `router_server.py`
  Receives browser GUI requests and applies lightweight routing rules.
- `hermes_supervisor.py`
  Acts as the scheduler/supervisor and forwards requests to the local `oMLX` OpenAI-compatible endpoint.
- `web/index.html`
  Minimal browser GUI for testing the pipeline.
- `HERMES_GATEWAY_INTEGRATION.md`
  Notes for wiring Weixin, WeCom, and Email through Hermes native gateway features.

## Quick Start

1. Copy the environment file:

```bash
cp .env.example .env
```

2. Edit `.env` to point to your local `oMLX` server.

3. Start the stack:

```bash
./start.sh
```

4. Open:

```text
http://127.0.0.1:8080
```

## Ports

- Router GUI/API: `8080`
- Hermes Supervisor API: `8090`

## Environment

Important settings in `.env`:

- `OMLX_BASE_URL`
- `OMLX_API_KEY`
- `DEFAULT_CHAT_MODEL`
- `DEFAULT_TTS_MODEL`
- `ROUTER_PORT`
- `SUPERVISOR_PORT`

## Request Flow

1. GUI posts a message to the router.
2. Router applies light rules:
   - TTS request
   - explicit model hint
   - explicit capability lane
   - keyword inference when capability is still `chat`
3. Router forwards the normalized task to Hermes Supervisor.
4. Supervisor calls the configured `oMLX` OpenAI-compatible API.
5. Response returns to the GUI.

## External Integrations

Use Hermes native messaging support for:

- Weixin (personal WeChat)
- WeCom (Enterprise WeChat)
- Email

Recommended production shape:

`GUI -> Router -> Hermes Supervisor -> oMLX`

`Weixin / WeCom / Email -> Hermes Gateway -> Hermes -> oMLX`

This keeps external transport, session handling, message delivery, attachments, and voice support inside Hermes where those features already exist.

## Notes

- This starter uses Python standard library only.
- External messaging adapters should not be reimplemented in this MVP when Hermes already provides them.
- If `OMLX_MOCK=true`, the supervisor returns a mock response so the pipeline can be tested without a running model server.
