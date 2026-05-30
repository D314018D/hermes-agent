_INGEST_PARAMETERS = {
    "type": "object",
    "properties": {
        "content": {"type": "string", "description": "Content to ingest."},
        "title": {"type": "string", "description": "Optional title for the note."},
        "source_type": {
            "type": "string",
            "enum": ["text", "voice", "file", "email"],
            "description": "Source modality. Defaults to text.",
        },
        "source_app": {"type": "string", "description": "Source app or platform label."},
        "captured_at": {"type": "string", "description": "ISO timestamp, if known."},
        "attachments": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Attachment paths or identifiers.",
        },
        "metadata": {"type": "object", "description": "Small JSON metadata object."},
        "sync_gbrain": {
            "type": "boolean",
            "description": "Run a GBrain import after a successful write.",
        },
        "dry_run": {
            "type": "boolean",
            "description": "Preview routing and review metadata without writing notes or GBrain logs.",
        },
    },
    "required": ["content"],
}

GBRAIN_INGEST = {
    "name": "gbrain_ingest",
    "description": (
        "GBrain-controlled durable memory ingestion boundary. Hermes must hand "
        "explicit save, capture, inbox, vault, meeting note, project note, decision, "
        "or durable memory requests here before any Obsidian Markdown rendering."
    ),
    "parameters": _INGEST_PARAMETERS,
}

OBSIDIAN_INGEST = {
    "name": "obsidian_ingest",
    "description": (
        "Compatibility alias for gbrain_ingest. Prefer gbrain_ingest for new calls; "
        "this old Obsidian-named tool still uses the same GBrain-controlled durable "
        "memory ingestion boundary."
    ),
    "parameters": _INGEST_PARAMETERS,
}

GBRAIN_IMPORT = {
    "name": "gbrain_import",
    "description": (
        "Import the Obsidian vault into GBrain. Use after ingestion or when the "
        "user asks to rebuild, sync, index, or refresh GBrain."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "vault_path": {
                "type": "string",
                "description": "Vault path. Defaults to the project obsidian-vault.",
            }
        },
    },
}

GBRAIN_MAINTAIN = {
    "name": "gbrain_maintain",
    "description": (
        "Run GBrain maintenance: embed stale items, extract links, extract timeline, "
        "and return stats. Use for scheduled maintenance or explicit rebuild requests."
    ),
    "parameters": {"type": "object", "properties": {}},
}

GBRAIN_QUERY = {
    "name": "gbrain_query",
    "description": (
        "Query GBrain for project/customer/factual context before answering questions "
        "that should use the durable Obsidian/GBrain knowledge layer."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Question or search query."}
        },
        "required": ["query"],
    },
}
