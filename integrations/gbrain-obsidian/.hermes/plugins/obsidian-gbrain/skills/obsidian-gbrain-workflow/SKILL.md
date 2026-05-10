# Obsidian + GBrain Workflow

Use this workflow when the user asks Hermes to save durable knowledge, query project memory, rebuild GBrain, or explain what the local brain knows.

## Storage

- Use `obsidian_ingest` for durable notes, inbox captures, project facts, meeting notes, decisions, and explicit save requests.
- Do not write Markdown directly unless the user explicitly asks for a manual file edit.
- Let the ingestion pipeline choose the destination page.

## Retrieval

- Use `gbrain_query` before answering factual questions about projects, customers, decisions, meetings, or historical local-brain state.
- If the query returns no useful context, say that GBrain did not have a relevant answer and then proceed from available context.

## Indexing

- Use `gbrain_import` after important ingestion if the user expects the new content to be searchable immediately.
- Use `gbrain_maintain` for rebuild, refresh, stale embedding, link extraction, timeline extraction, or scheduled maintenance requests.
