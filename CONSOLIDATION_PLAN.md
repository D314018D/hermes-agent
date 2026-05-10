# Hermes Consolidation Plan

Date: 2026-05-10

## Current State

- Live Hermes runs from `/Users/rl_home/.hermes/hermes-agent`.
- Live Hermes is on branch `codex/local-consolidation`.
- Live gateway is healthy at `http://127.0.0.1:8642/health`.
- This repository is the local integration and migration workspace, not the running Hermes core checkout.
- The GBrain/Obsidian plugin source in this repository matches the installed plugin at `/Users/rl_home/.hermes/plugins/obsidian-gbrain`, excluding Python cache files.

## Ownership Map

- Hermes core owns general runtime behavior, gateway routing, Apple Notes, and Apple Reminders.
- `apple_notes` is registered in the `terminal` toolset from live core.
- `remindctl` is registered in the `terminal` toolset from live core.
- GBrain/Obsidian belongs to the enabled `obsidian-gbrain` user plugin.
- The plugin exposes `obsidian_ingest`, `gbrain_import`, `gbrain_maintain`, and `gbrain_query`.

## Completed Checkpoints

- `98a17c173 chore: consolidate local Hermes integrations`
- `8d6db5ea5 chore: keep GBrain integration in plugin`

## Next Steps

1. Track the integration workspace intentionally, instead of committing every backup and discard file by accident.
2. Decide whether `integrations/gbrain-obsidian` should become the canonical source for the installed `obsidian-gbrain` plugin.
3. Use `scripts/sync_obsidian_gbrain_plugin.sh --check` to compare the repository plugin source with the installed user plugin.
4. Use `scripts/sync_obsidian_gbrain_plugin.sh --apply` only when intentionally updating `/Users/rl_home/.hermes/plugins/obsidian-gbrain` from this repository.
5. Add a smoke test that verifies `hermes plugins list` shows `obsidian-gbrain` enabled and gateway health returns `ok`.
6. Keep Apple Notes and Apple Reminders validation separate from GBrain/Obsidian plugin validation.

## Do Not Do

- Do not copy `integrations/gbrain-obsidian` wholesale into Hermes core.
- Do not re-add static `gbrain`, `obsidian`, or `obsidian-gbrain` toolsets to live core `toolsets.py`.
- Do not reintroduce core `tools/obsidian_tool.py` unless the plugin architecture is intentionally abandoned.
- Do not commit `__pycache__`, generated logs, or historical backup bundles as active source.
