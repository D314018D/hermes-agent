# Codex Task: Build Hermes → Obsidian → GBrain ingestion MVP

You are building a local-first ingestion system.

## Objective

Implement a minimal pipeline that accepts text, voice transcript, file text, or email text, then writes structured Markdown notes into the Obsidian vault.

## Required implementation order

1. Implement `ingestion/schema.py`
2. Implement `ingestion/classifier.py`
3. Implement `ingestion/scorer.py`
4. Implement `ingestion/renderer.py`
5. Implement `ingestion/router.py`
6. Implement `ingestion/pipeline.py`
7. Add CLI in `scripts/ingest.py`

## MVP behavior

Input JSON:

```json
{
  "source_type": "text",
  "source_app": "manual",
  "captured_at": "2026-04-25T14:00:00+10:00",
  "title": "Woolworths robot follow-up",
  "content": "Customer wants large robot test unit and certification timing.",
  "attachments": []
}
```

Output:

- Score the input.
- Classify it into one of: inbox, person, company, project, meeting, decision, document.
- Render a Markdown note with YAML frontmatter.
- Save it to the correct Obsidian directory.
- Print the path written.

## Important design rules

- Raw content should not be blindly saved unless `SAVE_RAW_CONTENT=true`.
- All durable knowledge must be summarized and structured.
- Use deterministic routing first. Only call LLM if classification confidence is low.
- File names must be slugified and date-prefixed where useful.
