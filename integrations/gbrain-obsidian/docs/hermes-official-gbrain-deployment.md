# Hermes Official Deployment With Obsidian + GBrain

This repository should treat Hermes as the deployed agent and Obsidian/GBrain as local-brain tools exposed to that agent.

## Recommended Architecture

```text
Weixin / Telegram / Open WebUI
        ↓
hermes gateway / Hermes API server
        ↓
Hermes AIAgent
        ↓
obsidian-gbrain plugin tools
        ↓
obsidian_ingest → GBrain classify/summarize/entities/index/graph → Markdown render → Obsidian vault
```

## Why This Replaces `scripts/hermes_dispatch.py`

`scripts/hermes_dispatch.py` is useful as a local smoke-test entrypoint, but it bypasses Hermes' official gateway sessions, plugin allow-list, tool registry, streaming, approvals, platform routing, background task support, and API server.

The active user plugin at `~/.hermes/plugins/obsidian-gbrain/` follows the official Hermes plugin model and points back to this repository's `integrations/gbrain-obsidian` project:

- `plugin.yaml` declares the plugin
- `schemas.py` describes tools for the model
- `tools.py` executes deterministic local work
- `__init__.py` registers tools into the `obsidian-gbrain` toolset

## Tools

- `obsidian_ingest`: canonical GBrain-first durable memory ingestion; renders Markdown into Obsidian after processing
- `gbrain_import`: imports the vault into GBrain; if the installed `gbrain` executable is Bun-based, Hermes resolves and invokes `bun` explicitly
- `gbrain_maintain`: embeds stale entries, extracts links/timeline, returns stats
- `gbrain_query`: queries GBrain before factual project/customer answers

Do not add `gbrain`, `obsidian`, or `obsidian-gbrain` as static Hermes core toolsets. Hermes core should discover these through the enabled user plugin.

## Enable In Development

```bash
export HERMES_OBSIDIAN_GBRAIN_ROOT="/Users/rl_home/.hermes/hermes-agent/integrations/gbrain-obsidian"
hermes plugins enable obsidian-gbrain
hermes gateway restart
```

Then verify inside Hermes:

```text
/plugins
/tools list
```

## Platform Guidance

- Weixin and Telegram should continue to enter through `hermes gateway`.
- Open WebUI should connect to Hermes' official API server at `http://127.0.0.1:8642/v1`.
- Scheduled GBrain refresh should use Hermes cron/background tools or a platform-level scheduled task that invokes `gbrain_maintain`.
- Apple Notes and Apple Reminders are separate Hermes core terminal tools (`apple_notes` and `remindctl`). They should not be routed through this Obsidian/GBrain plugin.

## GBrain Build Policy

- GBrain ingestion is the source of durable memory semantics.
- Obsidian Markdown is the human-editable render layer and can rebuild GBrain indexes.
- Use `gbrain_import` for immediate index refresh after important writes.
- Use `gbrain_maintain` for recurring rebuild/embedding/link/timeline maintenance.
- GBrain CLI calls are serialized by `maintenance/gbrain_cli.py` so multiple Hermes entrypoints do not collide on PGLite's local lock.
- Bun-backed `gbrain` shims require a resolvable `bun` binary; Hermes now treats missing Bun as an explicit dependency error instead of falling back to a brittle direct shim execution.
- For high-concurrency production use, prefer a server database backend such as Postgres/Supabase over local PGLite.

## Current Live State

- Live Hermes source: `/Users/rl_home/.hermes/hermes-agent`
- Live branch: `richard/hermes-local`
- Current gateway health endpoint: `http://127.0.0.1:8642/health`
- Plugin status: `obsidian-gbrain` is enabled as a user plugin.
- Core boundary: live Hermes no longer contains `tools/obsidian_tool.py` or static `gbrain`/`obsidian` toolsets.

## Local Model Policy

- A small local model can route simple capture/query tasks, but autonomous tool use needs a model that reliably follows tool schemas.
- Keep the router cheap and deterministic; reserve the larger local model for complex planning and multi-tool decisions.
- If the local model starts replying instead of calling tools, treat that as a model/tool-calling capability issue first, not an Obsidian ingestion issue.
- For the current local OMLX inventory, use `Qwen2.5-7B-Instruct-4bit` as the entry router and `Qwen3.5-9B-MLX-4bit` for complex/tool-heavy Hermes turns.
- Set `agent.tool_use_enforcement: true` for local non-GPT models; Hermes' `auto` mode only enables this reinforcement for GPT-family model names.
