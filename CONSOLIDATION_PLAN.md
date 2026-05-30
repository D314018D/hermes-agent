# Hermes Consolidation Plan

Date: 2026-05-10

## Current State

- Live Hermes runs from `/Users/rl_home/.hermes/hermes-agent`.
- Live Hermes core no longer carries an active `integrations/gbrain-obsidian` copy; the stale copy is archived under `dump/2026-05-29-hermes-mixed-copy-cleanup/stale-live-core/`.
- Live Hermes is on branch `richard/hermes-local`.
- Live gateway is healthy at `http://127.0.0.1:8642/health`.
- This repository is the local integration and migration workspace, not the running Hermes core checkout.
- The GBrain/Obsidian plugin source in this repository matches the installed plugin at `/Users/rl_home/.hermes/plugins/obsidian-gbrain`, excluding Python cache files and `.DS_Store`.

## Ownership Map

- Hermes core owns general runtime behavior, gateway routing, Apple Notes, and Apple Reminders.
- `apple_notes` is registered in the `terminal` toolset from live core.
- `remindctl` is registered in the `terminal` toolset from live core.
- GBrain/Obsidian belongs to the enabled `obsidian-gbrain` user plugin.
- The plugin exposes `gbrain_ingest`, compatibility alias `obsidian_ingest`, `gbrain_import`, `gbrain_maintain`, and `gbrain_query`.
- `obsidian_ingest`, `run_ingest`, and `tool_first_obsidian` are temporary compatibility aliases; review removal after 2026-06-29 once gateway logs and plugin callers have moved to GBrain-first names.

## Completed Checkpoints

- `98a17c173 chore: consolidate local Hermes integrations`
- `8d6db5ea5 chore: keep GBrain integration in plugin`
- Codex delegate overlay runtime plugin was installed after explicit approval.
- Codex delegate profile was installed after explicit approval.
- The stale launchd `HERMES_OBSIDIAN_GBRAIN_ROOT` path was corrected after explicit approval.

## Next Steps

1. Track the integration workspace intentionally, instead of committing every backup and discard file by accident.
2. Treat `integrations/gbrain-obsidian` as the canonical source for the installed `obsidian-gbrain` plugin.
3. Use `scripts/sync_obsidian_gbrain_plugin.sh --check` to compare the canonical plugin source with the installed user plugin.
4. Use `scripts/sync_obsidian_gbrain_plugin.sh --apply` only when intentionally updating `/Users/rl_home/.hermes/plugins/obsidian-gbrain` from this repository.
5. Add a smoke test that verifies `hermes plugins list` shows `obsidian-gbrain` enabled and gateway health returns `ok`.
6. Keep Apple Notes and Apple Reminders validation separate from GBrain/Obsidian plugin validation.
7. Keep future Codex delegate plugin/profile/launchd changes explicit, backed up, and reversible.
8. Keep historical backup bundles under `dump/` out of active source commits unless intentionally creating an archive branch.

## Do Not Do

- Do not copy `integrations/gbrain-obsidian` wholesale into Hermes core.
- Do not re-add static `gbrain`, `obsidian`, or `obsidian-gbrain` toolsets to live core `toolsets.py`.
- Do not reintroduce core `tools/obsidian_tool.py` unless the plugin architecture is intentionally abandoned.
- Do not commit `__pycache__`, generated logs, or historical backup bundles as active source.

## Codex Delegate Overlay

Date: 2026-05-30

The Codex delegate overlay lives at:

```text
/Users/rl_home/Documents/Codex/Hermes_Agent/overlays/codex-delegate
```

This overlay is the isolated development area for delegating complex engineering tasks from Hermes to Codex. It preserves these boundaries:

- Hermes remains the main agent, gateway, router, memory owner, and skills owner.
- Codex is only a delegated executor for complex coding, debugging, refactoring, automation, and multi-file analysis.
- Codex returns Task Summary, Memory Candidate, and Skill Candidate material only.
- Codex must not write Hermes core, GBrain raw database, Obsidian canonical notes, or Hermes skills.
- After explicit approval, the overlay is installed as a user plugin symlink at `/Users/rl_home/.hermes/plugins/codex-delegate`.
- After explicit approval, the optional Codex profile is installed at `~/.codex/codex-delegate.config.toml`.
- After explicit approval, the launchd `HERMES_OBSIDIAN_GBRAIN_ROOT` path correction was applied through the backed-up overlay script and Hermes gateway was restarted.
- Future changes should still treat plugin/profile/launchd operations as explicit local runtime changes, not default source edits.

Validation should use:

```bash
cd /Users/rl_home/Documents/Codex/Hermes_Agent/overlays/codex-delegate
./scripts/validate_overlay.sh
```
