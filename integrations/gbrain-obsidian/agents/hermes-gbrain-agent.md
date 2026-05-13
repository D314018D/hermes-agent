# Hermes + GBrain Agent Policy

## Role split

- Hermes is the reasoning and routing agent.
- Hermes memory is for short-term workflow/user preferences only.
- Obsidian/GBrain is the long-term knowledge layer.
- Ingestion is the gatekeeper between raw input and durable knowledge.

## Store vs skip

Store information when:
- It is useful beyond one month.
- It contains customer/project/decision/meeting information.
- It changes the state of a project.
- It creates or updates a person, company, project, or decision page.

Skip information when:
- It is casual chat.
- It is temporary debugging detail.
- It is already represented in a canonical note.
- It is low confidence and cannot be verified.

## Routing priority

1. Deterministic classification and routing.
2. LLM judgment only for ambiguous classification or summary.
3. Sub-agent only for heavy batch ingestion.

## Write rule

Never dump raw conversation into the brain by default.
Always summarize, structure, deduplicate, then write.

## Query rule

Before answering factual project/customer questions, query GBrain/Obsidian first.
