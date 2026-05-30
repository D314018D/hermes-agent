# Plans

## 2026-05-31 - Local oMLX Codex Profile

### Goal

Add a local Codex model profile for private/fallback engineering work while keeping Hermes as the first-level router and leaving Codex ChatGPT as the default non-private engineering path.

### Impact Review

- Target component: Codex delegate overlay and optional Codex user profile.
- Proposed change: add `local_private_coder` profile template, routing policy, validation, and documentation.
- Files likely changed: overlay configs, policies, scripts, tests, docs, and this plan.
- Impact on official GitHub updates: low; no live Hermes or oMLX source changes.
- Impact on local running services: low; validation reads Hermes/oMLX health but does not restart services.
- Risk level: medium because Codex profile syntax and oMLX auth must match the installed versions.
- Rollback method: remove `~/.codex/local_private_coder.config.toml`, restore any timestamped backup, and revert the overlay commit if needed.

### Implementation Notes

- Use Codex custom provider `wire_api = "responses"` because installed Codex rejects `wire_api = "chat"`.
- Use provider ID `localmlx`, not reserved provider IDs.
- Use `env_key = "OMLX_API_KEY"` and never persist the key in repository files.
- Install profile as `~/.codex/local_private_coder.config.toml`; do not change global `~/.codex/config.toml` defaults.
- Validate against oMLX `http://127.0.0.1:8000/v1` and model `Qwen3.5-4B-OptiQ-4bit`.

