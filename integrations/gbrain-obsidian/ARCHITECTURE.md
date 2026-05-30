# Hermes + GBrain + Obsidian Architecture

The canonical runtime flow is:

```text
Telegram / WeChat / Email / Voice
            ↓
Adapter Layer
            ↓
Normalizer
            ↓
Hermes Router
            ↓
GBrain Processing
    - classify
    - summarize
    - entity extraction
    - relation graph
    - embeddings
    - dedupe
            ↓
Memory Store
    - vector
    - graph
    - jsonl
            ↓
Markdown Renderer
            ↓
Obsidian Vault
```

Code mapping:

- Adapter Layer: `adapters/`
- Normalizer: `core/input_normalizer.py`
- Hermes Router: `routing/model_router.py` and `agent/runtime.py`
- GBrain Processing: `ingestion/gbrain_processing.py`
- Memory Store: `ingestion/memory_store.py`
- Markdown Renderer: `ingestion/renderer.py` and `ingestion/brain_page_writer.py`
- Obsidian Vault: `obsidian-vault/`

The live Hermes plugin entrypoint is `gbrain_ingest`, which calls the same ingestion pipeline. Direct Obsidian writes are not the durable-memory path; durable content must pass through GBrain Processing and Memory Store before rendering into the vault.
