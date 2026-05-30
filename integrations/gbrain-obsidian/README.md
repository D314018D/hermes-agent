# Hermes + GBrain + Obsidian Local Brain

This project connects Hermes, GBrain, and Obsidian into a local long-term memory workflow.

```text
Hermes = front-door agent / memory gate
GBrain = durable memory, indexing, embedding, query
Obsidian = human-readable Markdown, backlinks, MOC pages
Helper scripts = review processing, routing, wikilinks, MOC updates
```

The workflow is designed for a local Mac Mini setup, so it uses a **review-first** and **low-resource** approach.

---

## Core Workflow

```text
Telegram / WeChat / WebUI / File
        ↓
Hermes router / memory gate
        ↓
gbrain_ingest
        ↓
00_Inbox/Gbrain_Review
        ↓
gbrain import --no-embed
        ↓
optional gbrain embed --stale
        ↓
helper maintenance pipeline
(process_review / route_staging / update_mocs / check_backlinks)
        ↓
Obsidian final folders + backlinks + MOC pages
```

`obsidian_ingest` remains a compatibility alias for older Hermes calls through the next compatibility review after 2026-06-29; use `gbrain_ingest` for new calls.

`gbrain_ingest` is only a restricted handoff into:

```text
00_Inbox/Gbrain_Review
```

It must not write directly to final Obsidian folders, update MOCs, route notes, or modify existing notes unless the user explicitly asks for a manual file edit.

---

## Roles

### Hermes

Hermes handles:

- reasoning
- routing
- short-term context
- tools and skills
- memory-gate decisions

Hermes decides whether something is worth saving, but it should not directly write final Obsidian notes.

### gbrain_ingest

`gbrain_ingest` only writes durable memory candidates into:

```text
00_Inbox/Gbrain_Review
```

It does not classify, route, update MOCs, or write final pages.

### GBrain

GBrain handles:

- import / sync
- stale embedding
- query
- link extraction
- timeline extraction
- durable memory indexing

The configured GBrain brain path should point to the Obsidian vault root.

### Obsidian helper layer

Helper scripts handle:

- processing review notes
- generating wikilinks
- routing notes
- updating MOC pages
- checking backlinks

The helper layer is independent from official Hermes, GBrain, and Obsidian plugin code.

---

## Vault Structure

Expected vault structure:

```text
obsidian-vault/
├── 00_Inbox/
│   ├── Gbrain_Review/
│   ├── Gbrain_Staging/
│   └── Processed/
├── 01-people/
├── 02-companies/
├── 03-projects/
├── 04-meetings/
├── 05-decisions/
├── 06-skills/
├── 07-templates/
├── attachments/
└── brain/
```

Current recommended `brain_path` / `sync.repo_path`:

```text
/Users/rl_home/Documents/Codex/Hermes_Agent/integrations/gbrain-obsidian/obsidian-vault
```

Use the vault root, not the Hermes Agent repo and not the mostly empty `obsidian-vault/brain/` folder.

---

## Storage Rules

- Default mode should remain read-only.
- Only save durable knowledge.
- New memory candidates should first go to `00_Inbox/Gbrain_Review`.
- Do not write directly to final Obsidian folders unless the user explicitly asks for a manual file edit.
- Do not bypass the review pipeline for long-term memory writes.
- Let the helper pipeline classify, linkify, route, update MOCs, and check backlinks.

---

## Write Permission Model

### Read-only mode

Default mode.

Allowed:

- `gbrain_query`
- inspection
- config checks
- dry-run maintenance
- read-only Obsidian review

Blocked:

- writing Markdown
- moving files
- routing notes
- updating MOCs
- running maintenance with `--write`
- changing configs
- installing cron

### Restricted write mode

Allowed only when the user explicitly asks to save durable knowledge.

Restricted writes may only target:

```text
00_Inbox/Gbrain_Review
```

### Save-intent escalation

When the user clearly expresses a save intent, such as:

- "remember this"
- "save this"
- "write this to GBrain"
- "write this to Obsidian"
- "add this to memory"
- "保存这个"
- "记住这个"
- "写入 GBrain"
- "写入 Obsidian"

Hermes may temporarily escalate from read-only inspection to a restricted write action.

This is **not** a global write mode.

The only allowed write action is:

```text
gbrain_ingest → 00_Inbox/Gbrain_Review
```

The following actions remain blocked unless the user explicitly approves a maintenance write or manual edit:

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

After the restricted write is complete, the system should return to read-only mode.

### Maintenance write mode

Allowed only when the user explicitly approves or runs a maintenance write command:

```bash
scripts/gbrain_obsidian/run_maintenance.sh --write --limit 3
```

Always run dry-run first.

---

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

Skip:

- ordinary rewrites
- ordinary translations
- one-off casual questions
- temporary debugging with no final conclusion
- low-value duplicates
- low-confidence summaries

When uncertain, write to Review, not to final folders.

---

## Retrieval Rules

Use `gbrain_query` before answering factual questions about:

- projects
- customers
- decisions
- meetings
- historical local-brain state
- previous technical configuration
- local workflow history

Prefer GBrain over model memory for local project facts.

If GBrain has no useful context, say so and proceed from available context.

---

## Indexing Rules

After important ingestion, use the lightweight discovery step:

```bash
gbrain import --no-embed
```

Use stale embedding only when needed:

```bash
gbrain embed --stale
```

Do not run embedding for every new note unless the user expects it to be searchable immediately.

Avoid high-frequency embedding jobs on the Mac Mini. Prefer manual, event-driven, or nightly maintenance.

---

## Manual Maintenance

From the integration root:

```bash
cd "/Users/rl_home/Documents/Codex/Hermes_Agent/integrations/gbrain-obsidian"
```

Dry-run first:

```bash
scripts/gbrain_obsidian/run_maintenance.sh --dry-run --limit 10
```

Small write test:

```bash
scripts/gbrain_obsidian/run_maintenance.sh --write --limit 3
```

Make new content searchable when needed:

```bash
gbrain embed --stale
```

Query GBrain:

```bash
gbrain query "Hermes GBrain Obsidian workflow"
```

---

## Helper Scripts

Helper scripts live under:

```text
scripts/gbrain_obsidian/
```

Main scripts:

```text
common.py
process_review.py
route_staging.py
update_mocs.py
check_backlinks.py
run_gbrain_extract.py
run_maintenance.sh
```

Expected behavior:

- default to dry-run
- preserve raw review notes
- avoid destructive moves
- prevent duplicate MOC links
- report broken links and orphan notes
- support small batch processing

---

## MOC and Wikilinks

MOC means **Map of Content**.

MOC pages are navigation pages such as:

```text
03-projects/Woolworths.md
02-companies/Hanshow.md
01-people/Ben.md
06-skills/NFC.md
```

Wikilinks should be generated only for high-value entities:

```text
Woolworths → [[Woolworths]]
Hanshow → [[Hanshow]]
Smart Trolley → [[Smart Trolley]]
NFC → [[NFC]]
GBrain → [[GBrain]]
Hermes → [[Hermes]]
oMLX → [[oMLX]]
```

Avoid over-linking ordinary words.

---

## Resource Protection

This workflow is designed for a local Mac Mini environment.

Rules:

- no high-frequency embedding jobs
- no concurrent embedding jobs
- use shared GBrain lock where applicable
- skip maintenance if another GBrain job is running
- use small write batches first
- skip large Markdown files by default
- refuse writes when disk space is low
- dry-run before write

---

## Environment

Important settings:

```text
OBSIDIAN_VAULT_PATH
GBRAIN_DRY_RUN
GBRAIN_AUTO_COMMIT
HERMES_OBSIDIAN_WRITE_MODE
```

Recommended safety defaults:

```text
GBRAIN_AUTO_COMMIT=false
HERMES_OBSIDIAN_WRITE_MODE=read_only
```

Explicit save requests may use restricted `gbrain_ingest` writes to:

```text
00_Inbox/Gbrain_Review
```

Weather/API secrets used by Hermes itself belong in:

```text
~/.hermes/.env
```

This integration should only keep Obsidian/GBrain ingestion settings.

---

## Scheduling

Do not install cron by default.

For this local workflow, prefer:

```text
manual maintenance
event-driven embedding
low-frequency sync/import
nightly maintenance only after approval
```

Do not run `embed --stale` every 15 minutes.

---

## Safety and Rollback

The helper layer is isolated under:

```text
scripts/gbrain_obsidian/
logs/gbrain_obsidian/
docs/local-gbrain-obsidian-maintenance.md
```

Rollback is simple:

```text
delete the helper scripts/logs/docs
restore the previous GBrain sync.repo_path if needed
```

Do not delete the GBrain DB or Obsidian vault as part of normal rollback.

---

## Memory Rule

Hermes should not remember everything.

Hermes remembers workflow rules, user preferences, and short-term context.

GBrain stores durable project knowledge and makes it searchable.

Obsidian renders editable Markdown, backlinks, and MOC pages for human review.
