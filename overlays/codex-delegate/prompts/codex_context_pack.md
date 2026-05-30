# Codex Context Pack Schema

Hermes passes a structured Context Pack to Codex. Codex must not infer missing permissions from ambient access.

```yaml
task_id: "..."
task_hash: "sha256:..."
user_goal: "..."
privacy_level: "public | private | secret"
route_reason: "..."
recent_context_summary: "..."
relevant_memory_summary: "..."
allowed_working_directory: "..."
allowed_read_paths:
  - "..."
allowed_write_paths:
  - "..."
forbidden_paths:
  - "/Users/rl_home/.hermes/hermes-agent"
  - "/Users/rl_home/.gbrain/brain.pglite"
  - "Obsidian canonical vault paths unless explicitly approved"
network_policy: "disabled | restricted | allowed"
api_fallback_allowed: false
api_fallback_approved: false
output_required:
  - final_answer
  - task_summary
  - memory_candidate
  - skill_candidate
```

If a field is missing, use the safer default: private, local-only, no API fallback, and no durable writes.
