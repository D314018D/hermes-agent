CODEX_DELEGATE = {
    "name": "codex_delegate",
    "description": (
        "Delegate an approved complex engineering task to Codex under Hermes "
        "control. The tool enforces privacy boundaries, strips API fallback by "
        "default, and returns final_answer, task_summary, memory_candidate, and "
        "skill_candidate. Do not use for ordinary chat, durable memory writes, "
        "or secret/private cloud fallback."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "task_id": {"type": "string", "description": "Hermes task identifier."},
            "task_hash": {"type": "string", "description": "Stable task hash if already known."},
            "user_goal": {"type": "string", "description": "Delegated engineering goal."},
            "privacy_level": {
                "type": "string",
                "enum": ["public", "private", "secret"],
                "description": "Hermes-classified privacy level.",
            },
            "route_reason": {"type": "string", "description": "Why Hermes selected Codex delegation."},
            "recent_context_summary": {"type": "string", "description": "Non-sensitive context summary."},
            "relevant_memory_summary": {"type": "string", "description": "Hermes-reviewed memory summary."},
            "allowed_working_directory": {"type": "string", "description": "Working directory for Codex."},
            "allowed_read_paths": {"type": "array", "items": {"type": "string"}},
            "allowed_write_paths": {"type": "array", "items": {"type": "string"}},
            "forbidden_paths": {"type": "array", "items": {"type": "string"}},
            "network_policy": {
                "type": "string",
                "enum": ["disabled", "restricted", "allowed"],
                "description": "Network policy selected by Hermes.",
            },
            "api_fallback_allowed": {"type": "boolean", "description": "Whether API fallback may be requested."},
            "api_fallback_approved": {"type": "boolean", "description": "One-time approved API fallback flag."},
            "dry_run": {"type": "boolean", "description": "Validate without invoking Codex."},
        },
        "required": ["user_goal", "privacy_level"],
    },
}
