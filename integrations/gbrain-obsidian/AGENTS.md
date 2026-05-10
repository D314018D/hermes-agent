# Workspace Rules

This repository uses Hermes as the front door, but durable note writes must go
through the deterministic ingestion pipeline.

## Obsidian writes

- When the user asks to save, capture, store, or write something into
  Obsidian, the vault, or inbox, do not create Markdown notes directly with
  generic file tools unless the user explicitly asks for a manual edit.
- Default to review-first writes. New durable content should land in
  `obsidian-vault/00_Inbox/Gbrain_Review/` unless a reviewed workflow explicitly
  enables `GBRAIN_AUTO_COMMIT=true`.
- Use `GBRAIN_DRY_RUN=true` or `python3 scripts/ingest.py --dry-run ...` before
  new bulk ingestion, route changes, or uncertain file movement.
- Do not delete source files after parsing/transcription unless the payload
  explicitly opts into `delete_original_after_processing`.
- Prefer the ingestion entrypoint:

```bash
python3 scripts/ingest.py -
```

- Pass JSON on stdin with at least:
  - `source_type`
  - `source_app`
  - `captured_at`
  - `title`
  - `content`
  - `attachments`
- Let `ingestion/page_resolver.py` choose the final destination. For inbox
  cases, the canonical review location is
  `obsidian-vault/00_Inbox/Gbrain_Review/`.

## Model routing questions

- When the user asks which model is active, why a route was chosen, or whether
  OMLX selected another model, do not answer from conversation memory alone.
- Inspect `config/model_routes.yaml`.
- Prefer running:

```bash
python3 scripts/route_model.py "<user request>" --router --llm
```

- If the answer concerns historical routing, also inspect
  `obsidian-vault/06-skills/current-model-routing.md`.

## General

- Obsidian/GBrain is the durable memory layer.
- Hermes memory should not replace the vault.
- Deterministic routing is preferred over ad hoc note-path guessing.
- Hermes-wide API secrets, including weather API keys for chat/weather cron
  tasks, belong in `~/.hermes/.env`; do not place them in this integration's
  `.env`.
