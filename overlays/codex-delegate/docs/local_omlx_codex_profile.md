# Local oMLX Codex Profile

Date: 2026-05-31

## Purpose

`local_private_coder` gives Codex an isolated local oMLX path for private engineering work and private fallback. It does not replace Hermes as router, memory owner, or skills owner.

## Current Compatibility Decision

The downloaded setup guide suggested `wire_api = "chat"` for local OpenAI-compatible endpoints. The installed Codex CLI rejects that value for custom providers, so this overlay uses:

```toml
wire_api = "responses"
```

This matches the current oMLX server source, which exposes `/v1/responses` for Codex compatibility.

## Installed Profile

Source template:

```text
/Users/rl_home/Documents/Codex/Hermes_Agent/overlays/codex-delegate/configs/local_private_coder.config.toml
```

Install target:

```text
/Users/rl_home/.codex/local_private_coder.config.toml
```

Key settings:

```toml
model = "Qwen3.5-4B-OptiQ-4bit"
model_provider = "localmlx"

[model_providers.localmlx]
base_url = "http://127.0.0.1:8000/v1"
env_key = "OMLX_API_KEY"
wire_api = "responses"
```

The profile uses `OMLX_API_KEY` at runtime. The key must not be committed, logged, or written into Hermes default environment.

## Validation

Run from the overlay:

```bash
./scripts/validate_overlay.sh
```

For live Codex profile validation, export `OMLX_API_KEY` in the current shell only, then run a read-only prompt:

```bash
codex --strict-config --profile local_private_coder exec \
  "Reply with OK only. Do not inspect, create, modify, or delete files."
```

## Rollback

Remove the installed profile:

```bash
rm ~/.codex/local_private_coder.config.toml
```

Or run the overlay rollback helper:

```bash
./scripts/rollback_overlay.sh
```
