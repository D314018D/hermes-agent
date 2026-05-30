# Obsidian + GBrain Workflow

Use this workflow when the user asks Hermes to save durable knowledge, query project memory, rebuild GBrain, refresh embeddings, or explain what the local brain knows.

## Roles

- Hermes is the front-door agent, router, and memory gate.
- `gbrain_ingest` is only a restricted handoff into the GBrain-controlled ingestion boundary.
- GBrain owns durable memory, import/sync, embedding, query, link extraction, timeline extraction, and local memory indexes.
- Obsidian helper scripts handle review processing, wikilinks, routing, MOC updates, and backlink checks.
- Obsidian is the human-readable Markdown editing and visualization surface.

## Storage

- Default mode should remain read-only.
- Use `gbrain_ingest` only as a restricted handoff to the GBrain-controlled ingestion boundary.
- New durable memory candidates should first be written to `00_Inbox/Gbrain_Review`.
- Do not write Markdown directly to final Obsidian folders unless the user explicitly asks for a manual file edit.
- `gbrain_ingest` must not classify, route, update MOCs, or modify existing notes.
- Let the GBrain/Obsidian helper pipeline classify, linkify, route, update MOCs, and check backlinks.
- Do not bypass the ingestion pipeline for long-term memory writes.

## Write Permission

- Read-only mode allows retrieval, inspection, and dry-run only.
- Only when the user explicitly asks to save durable knowledge, allow a restricted write through `gbrain_ingest`.
- Restricted writes may only target `00_Inbox/Gbrain_Review`.
- This restricted write is not a global write mode.
- After the restricted write is complete, return to read-only mode.
- Final-folder writes, MOC updates, routing, file moves, backlink changes, and maintenance `--write` actions require explicit user approval.
- Never disable read-only globally just to make ingestion easier.

## Save-intent Escalation

Treat the following as clear save intent:

- "remember this"
- "save this"
- "write this to GBrain"
- "write this to Obsidian"
- "add this to memory"
- "保存这个"
- "记住这个"
- "写入 GBrain"
- "写入 Obsidian"

When clear save intent is present, Hermes may temporarily allow this restricted write only:

```text
gbrain_ingest → 00_Inbox/Gbrain_Review
```

The following actions remain blocked unless separately approved:

```text
writing to final Obsidian folders
routing notes
updating MOC pages
moving files
modifying existing notes
running maintenance with --write
changing GBrain/Hermes/oMLX configuration
installing cron or launchd jobs
```

## Memory Gate

Do not save every conversation.

Save only durable knowledge, such as:

- project or customer facts
- decisions
- meeting outcomes
- reusable technical workflows
- system configuration changes
- user-approved long-term preferences
- important problem-and-resolution records
- facts that should be recalled later

Skip:

- ordinary rewrites
- ordinary translations
- one-off casual questions
- temporary debugging with no final conclusion
- low-value duplicates
- low-confidence summaries
- sensitive content without a clear durable purpose

When uncertain, write to `00_Inbox/Gbrain_Review`, not to final folders.

## Retrieval

- Use `gbrain_query` before answering factual questions about projects, customers, decisions, meetings, or historical local-brain state.
- Use `gbrain_query` before answering questions about previous local technical configuration, local workflow history, or what the local brain knows.
- Prefer GBrain retrieval over model memory for local project facts.
- If GBrain returns no useful context, say that GBrain did not have a relevant answer and proceed from available context.

## Indexing

- After important ingestion, use the local lightweight discovery step, currently `gbrain_import --no-embed`, so GBrain can discover the new note.
- Do not run embedding immediately for every new note unless the user expects the content to be searchable immediately.
- Use `gbrain_maintain` or the helper maintenance script for stale embedding, link extraction, timeline extraction, MOC updates, backlink checks, rebuilds, refreshes, or scheduled maintenance.
- Prefer stale/incremental indexing over full rebuilds.
- Avoid high-frequency embedding jobs on the Mac Mini; prefer event-driven, manual, or nightly maintenance.

## Recommended Flow

```text
1. Hermes/GBrain memory gate decides whether the content is worth saving.
2. If allowed, `gbrain_ingest` writes a review note to `00_Inbox/Gbrain_Review`.
3. Run `gbrain_import --no-embed` as the lightweight sync/discovery step.
4. Later, run `embed --stale` during maintenance or when immediate semantic search is needed.
5. Run review/routing/MOC/backlink helper scripts.
6. Final structured notes and backlinks appear in Obsidian.
```

## Maintenance

- Always run dry-run before write.
- Use small write batches first.
- Do not install cron by default.
- Do not run `embed --stale` every 15 minutes on the Mac Mini.
- Prefer manual, event-driven, or approved nightly maintenance.
- Use shared GBrain locking where applicable.
- Skip maintenance if another GBrain or embedding process is already running.

Recommended manual commands:

```bash
scripts/gbrain_obsidian/run_maintenance.sh --dry-run --limit 10
scripts/gbrain_obsidian/run_maintenance.sh --write --limit 3
gbrain embed --stale
```

## Safety

- Do not modify official Hermes, GBrain, or Obsidian plugin repositories for local helper behavior.
- Keep helper scripts isolated under `scripts/gbrain_obsidian/`.
- Keep logs isolated under `logs/gbrain_obsidian/`.
- Do not delete the GBrain DB or Obsidian vault as part of normal rollback.
- Do not change GBrain/Hermes/oMLX configuration unless explicitly requested.


`obsidian_ingest` remains a compatibility alias for older Hermes calls through the next compatibility review after 2026-06-29; use `gbrain_ingest` for new calls.
