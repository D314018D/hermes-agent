# Local Hermes GBrain Tooling Tightening - 2026-05-30

## Reason

Keep runtime messaging paths aligned with the GBrain-first durable memory architecture:

```text
Hermes router -> gbrain_ingest / run_gbrain_ingest -> GBrain review-first pipeline -> Obsidian vault rendering
```

## Changes

- Updated `~/.hermes/.env` so `WEIXIN_DEFAULT_MODEL` uses `Qwen3.5-4B-OptiQ-4bit` instead of the stale Qwen2.5 model.
- Updated the live gateway durable-memory annotation in `~/.hermes/hermes-agent/gateway/run.py` to prefer `gbrain_ingest`; `obsidian_ingest` is documented as compatibility alias only.
- Removed direct `obsidian` toolset exposure from messaging/API platform toolsets in `~/.hermes/config.yaml` while leaving CLI manual access intact.

## Upgrade Impact

`~/.hermes/hermes-agent/gateway/run.py` is live Hermes core code. This is a local patch and may be overwritten by a future Hermes update. Keep the patch small and re-review after upstream updates.

## Rollback

Rollback snapshots were saved under:

```text
/Users/rl_home/Documents/Codex/Hermes_Agent/dump/2026-05-30-hermes-gbrain-tooling-tighten/prechange/
```

To roll back, restore the corresponding snapshot files to:

```text
/Users/rl_home/.hermes/.env
/Users/rl_home/.hermes/config.yaml
/Users/rl_home/.hermes/hermes-agent/gateway/run.py
```

Then restart Hermes gateway.
