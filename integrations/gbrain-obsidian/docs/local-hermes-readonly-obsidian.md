# Local Hermes Read-Only Obsidian Boundary

## Reason

Hermes should be able to query Obsidian/GBrain context, but it must not write Markdown directly into the Obsidian vault. Durable writes should be owned by GBrain-controlled ingestion and maintenance flows so the vault's frontend Markdown format stays deterministic.

## Files Changed

- `.env`
- `.env.example`
- `ingestion/pipeline.py`
- `agent/runtime.py`
- `config/model_routes.yaml`
- `tests/test_pipeline_voice.py`
- `tests/test_hermes_dispatch.py`
- `docs/local-hermes-readonly-obsidian.md`
- `/Users/rl_home/.hermes/plugins/obsidian-gbrain/tools.py`
- `/Users/rl_home/.hermes/plugins/obsidian-gbrain/schemas.py`
- `/Users/rl_home/.hermes/plugins/obsidian-gbrain/skills/obsidian-gbrain-workflow/SKILL.md`
- `/Users/rl_home/Library/LaunchAgents/ai.hermes.gateway.plist`

## Policy

`HERMES_OBSIDIAN_WRITE_MODE=read_only` blocks vault writes when ingestion is invoked by Hermes-facing sources such as `hermes_plugin` or `*_agent`.

`GBRAIN_AUTO_COMMIT=false` keeps generated content in review-first mode when a non-Hermes GBrain ingestion path is explicitly used.

The active `obsidian-gbrain` Hermes user plugin now falls back to this project path instead of the stale copy under `~/.hermes/hermes-agent/integrations/gbrain-obsidian`.

The Hermes LaunchAgent exports `HERMES_OBSIDIAN_GBRAIN_ROOT` and `HERMES_OBSIDIAN_WRITE_MODE=read_only` as runtime guards.

GBrain maintenance, import, and query commands are not blocked by this Hermes write guard.

## Upgrade Impact

Low. This is a project-local guard in the integration layer and does not modify Hermes core, upstream GBrain, Obsidian, oMLX, or official plugin package code.

The active Hermes gateway must be restarted after plugin or launchd environment changes.

## Rollback

Set `HERMES_OBSIDIAN_WRITE_MODE=write_enabled` or remove the variable, then restart Hermes if it is already running.

Set `GBRAIN_AUTO_COMMIT=true` only if final vault writes should bypass review for high-confidence captures.

To restore the previous launchd environment, copy `/Users/rl_home/Library/LaunchAgents/ai.hermes.gateway.plist.bak-hermes-obsidian-readonly-20260523` back to `/Users/rl_home/Library/LaunchAgents/ai.hermes.gateway.plist`, then reload the LaunchAgent.
