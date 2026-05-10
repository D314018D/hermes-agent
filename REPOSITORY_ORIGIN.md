# Repository Origin

- Source machine: `MacMini01`
- Workspace path: `/Users/rl_home/Documents/Codex/Hermes Agent`
- Bootstrap method: local GitHub CLI repo creation, then GitHub MCP metadata commit

## Live Hermes Relationship

- Running Hermes source: `/Users/rl_home/.hermes/hermes-agent`
- Running Hermes branch after consolidation: `codex/local-consolidation`
- Live Hermes upstream: `https://github.com/NousResearch/hermes-agent.git`
- This workspace is not the live Hermes core checkout. Treat it as the local integration, documentation, plugin source, backups, and migration workspace.

## Ownership Boundary

- Hermes core changes belong in `/Users/rl_home/.hermes/hermes-agent` and should stay limited to generally useful Hermes behavior.
- Apple Notes support is a live core tool: `tools/apple_notes_tool.py`, exposed as `apple_notes` in the `terminal` toolset.
- Apple Reminders support is a live core tool path: `tools/remindctl_tool.py` plus `tools/remindctl_terminal_broker.py`, exposed as `remindctl` in the `terminal` toolset.
- GBrain and Obsidian are project-local plugin responsibilities, not Hermes core responsibilities.
- The active GBrain/Obsidian plugin is installed at `/Users/rl_home/.hermes/plugins/obsidian-gbrain` and points back to this workspace's `integrations/gbrain-obsidian` project.

## Consolidation Checkpoints

- `98a17c173 chore: consolidate local Hermes integrations`: Apple Notes, Reminders hardening, gateway steering, and local integration checkpoint in the live Hermes repo.
- `8d6db5ea5 chore: keep GBrain integration in plugin`: removed hardcoded core Obsidian/GBrain tool registration and kept GBrain/Obsidian behind the enabled `obsidian-gbrain` plugin.

## Deployment Rule

Do not copy `integrations/gbrain-obsidian` into Hermes core. Keep the plugin enabled with `hermes plugins enable obsidian-gbrain`, restart `hermes gateway`, and verify via `hermes plugins list` plus `http://127.0.0.1:8642/health`.
