# Hermes + GBrain + Obsidian Local Brain Starter

Goal: use Hermes as the front-door agent, GBrain as the durable memory processing layer, and Obsidian as the human-readable Markdown editing layer.

## Roles

- Hermes: reasoning, routing, short-term memory, tools, skills.
- Ingestion layer: normalize, classify, score, summarize, deduplicate, and route.
- GBrain: classify, summarize, extract entities/relations, maintain vector/graph indexes, and own durable memory semantics.
- Obsidian Vault: human-readable Markdown rendering and editing surface.

## Recommended flow

```text
Telegram / WeChat / WebUI / File
        ↓
Input Adapter / Normalize
        ↓
Hermes router / orchestrator
        ↓
obsidian_ingest
        ↓
GBrain core memory processing
        ↓
Render Markdown
        ↓
Obsidian human editing layer
```

## MVP setup

1. Open `obsidian-vault/` as an Obsidian Vault.
2. Optional: install Obsidian Local REST API plugin if you want API writes.
3. Configure `.env.example` into `.env`.
4. Give Codex `CODEX_TASK.md`.
5. Start by implementing `ingestion/pipeline.py`.

## Local ingestion

Run any connector JSON through the local CLI:

```bash
python3 scripts/ingest.py connectors/text/example_input.json
python3 scripts/ingest.py connectors/voice/example_input.json
python3 scripts/ingest.py connectors/file/example_input.json
python3 scripts/ingest.py connectors/email/example_input.json
```

The CLI also accepts JSON on stdin with `python3 scripts/ingest.py -`.

## Hermes task dispatch

For official deployment, expose this project's Obsidian/GBrain actions through
the enabled Hermes user plugin in `~/.hermes/plugins/obsidian-gbrain/`, then let
`hermes gateway` or Hermes' API server handle WeChat, Telegram, and WebUI input.

In the current live deployment, Hermes core lives at
`/Users/rl_home/.hermes/hermes-agent` and this project stays outside core as the
plugin's working root. Keep that boundary: Apple Notes and Apple Reminders are
Hermes core terminal tools, while GBrain/Obsidian ingestion belongs to this
plugin.

`scripts/hermes_dispatch.py` is kept as a local smoke-test entrypoint rather
than the production dispatch path:

```bash
cat payload.json | python3 scripts/hermes_dispatch.py -
```

Supported text entry sources include WeChat, Telegram, and WebUI/local_web.
The dispatcher will normalize the payload, run the router, let Hermes choose a
tool from the local registry, and then execute it.

Example payload:

```json
{
  "source": "wechat",
  "source_type": "wechat_text",
  "text": "请把这条信息写入 Obsidian inbox",
  "chat_id": "o9cq...",
  "message_id": "msg-123",
  "timestamp": "2026-05-05T09:00:00+10:00"
}
```

Runtime traces are appended to `logs/hermes-dispatch.jsonl`, and queued async
tasks are appended to `logs/hermes-task-queue.jsonl`.

See `docs/hermes-official-gbrain-deployment.md` for the recommended Hermes
gateway/API server deployment shape, including GBrain import, maintenance, and
query tools.

Useful environment variables:

- `OBSIDIAN_VAULT_PATH`: defaults to `./obsidian-vault`
- `MIN_STORE_SCORE`: defaults to `2`
- `SAVE_RAW_CONTENT`: defaults to `false`; set to `true` only when raw source text should be stored
- `GBRAIN_DRY_RUN`: defaults to `false`; set to `true` or pass `--dry-run` to preview without writing notes or memory logs
- `GBRAIN_AUTO_COMMIT`: defaults to `false`; keep review-first safety unless explicitly enabling high-confidence final writes

Weather/API secrets used by Hermes itself, such as `OPENWEATHER_API_KEY`, belong
in `~/.hermes/.env`, not this integration's `.env`. This integration should only
keep Obsidian/GBrain ingestion settings.

## Review-first workflow

The safe default is now:

```text
Input source -> Hermes -> GBrain processing -> 00_Inbox/Gbrain_Review -> explicit final commit
```

Generated review notes include YAML fields for `source`, `status`,
`review_status`, `client`, `project`, `solution`, `type`, `sensitivity`,
`confidence`, `suggested_folder`, and `final_folder`. Low-confidence,
commercial-sensitive, legal-review, unknown-client, and duplicate items stay in
`00_Inbox/Gbrain_Review`.

Use `python3 scripts/ingest.py --dry-run input.json` before testing new routing
or bulk ingestion. Safe final commit helpers copy from review to final folders
without deleting the review note and create a backup before overwriting an
existing final note.

## Memory rule

Do not ask Hermes to remember everything. Hermes remembers workflow/user preferences. GBrain stores durable project knowledge and renders editable Markdown into Obsidian.
