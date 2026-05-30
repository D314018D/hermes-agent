# Codex → Hermes End-to-End Configuration Optimization Guide

**Purpose:** Give Codex CLI a safe, upgrade-compatible plan for optimizing Richard's local Hermes Agent environment while keeping Hermes as the main agent and adding Codex only as a delegated high-capability executor.

**Date:** 2026-05-30
**Owner:** Richard Liu
**Primary rule:** Hermes remains the main agent, memory owner, skills owner, and gateway. Codex is only an external delegated executor.

---

## 0. Executive Summary

Do **not** replace Hermes with Codex.

The target architecture is:

```text
WeChat / Telegram / Web / Voice
        ↓
Hermes Agent live gateway
        ↓
Local model routing: 2B / 4B / 9B
        ↓
Hermes handles normal/private/memory tasks locally
        ↓
Codex CLI is invoked only for complex coding/execution tasks
        ↓
Codex returns Task Summary / Memory Candidate / Skill Candidate
        ↓
Hermes reviews
        ↓
Approved memory goes through existing GBrain ingest pipeline
        ↓
GBrain processes and eventually persists / reflects into Obsidian
```

The system must preserve:

```text
1. Hermes official upgrade compatibility
2. Hermes built-in learning loop and skills generation
3. Existing GBrain → Obsidian memory pipeline
4. Local privacy-first model routing
5. ChatGPT Codex entitlement-first token strategy
6. OpenAI API off by default
7. No direct Codex writes to Hermes core, GBrain raw DB, or Obsidian canonical notes
```

---

## 1. Verified Local Environment Boundaries

### 1.1 Live Hermes runtime repo

```text
/Users/rl_home/.hermes/hermes-agent
```

This is the real live Hermes runtime and upgrade repo.

Known facts:

```text
Official upstream:
https://github.com/NousResearch/hermes-agent.git

Personal fork remote:
origin -> https://github.com/D314018D/hermes-agent.git

Current live branch:
richard/hermes-local

Upgrade strategy:
main = official clean mirror
richard/hermes-local = local runtime modifications
```

Live CLI / gateway path:

```text
/Users/rl_home/.local/bin/hermes
  -> /Users/rl_home/.hermes/hermes-agent/venv/bin/hermes

Gateway launchd:
/Users/rl_home/Library/LaunchAgents/ai.hermes.gateway.plist

Gateway process:
/Users/rl_home/.hermes/hermes-agent/venv/bin/python -m hermes_cli.main gateway run --replace

Gateway health:
http://127.0.0.1:8642/health
Expected: {"status":"ok","platform":"hermes-agent"}
```

**Codex must not modify this repo by default.**

Codex may read it for inspection, but write operations require explicit approval and must follow `docs/HERMES_LOCAL_GIT_WORKFLOW.md`.

---

### 1.2 Hermes integration / Codex work area

```text
/Users/rl_home/Documents/Codex/Hermes_Agent
```

This is not the current live Hermes core. It is the local integration, migration, plugin, and documentation work area.

Existing important paths:

```text
/Users/rl_home/Documents/Codex/Hermes_Agent/REPOSITORY_ORIGIN.md
/Users/rl_home/Documents/Codex/Hermes_Agent/CONSOLIDATION_PLAN.md
/Users/rl_home/Documents/Codex/Hermes_Agent/integrations/gbrain-obsidian/docs
```

This is the correct parent location for the Codex delegate overlay.

---

### 1.3 Existing active plugin

```text
Enabled plugin:
/Users/rl_home/.hermes/plugins/obsidian-gbrain

Source:
/Users/rl_home/Documents/Codex/Hermes_Agent/integrations/gbrain-obsidian
```

The Codex delegate should follow the same pattern:

```text
Source / development:
/Users/rl_home/Documents/Codex/Hermes_Agent/overlays/codex-delegate

Installed plugin / runtime overlay:
/Users/rl_home/.hermes/plugins/codex-delegate
```

Do not mix Codex delegate code into Hermes core.

---

## 2. Recommended Directory Layout

Create or use this project directory:

```text
/Users/rl_home/Documents/Codex/Hermes_Agent/overlays/codex-delegate
```

Recommended structure:

```text
/Users/rl_home/Documents/Codex/Hermes_Agent/overlays/codex-delegate/
├── AGENTS.md
├── README.md
├── docs/
│   └── codex_hermes_end_to_end_optimization_guide.md
├── tools/
│   └── codex_delegate.py
├── configs/
│   └── codex_delegate.yaml
├── policies/
│   ├── routing_policy.yaml
│   ├── privacy_policy.yaml
│   └── memory_policy.yaml
├── prompts/
│   ├── codex_context_pack.md
│   └── codex_task_summary_schema.md
├── scripts/
│   ├── inspect_environment.sh
│   ├── install_overlay.sh
│   ├── validate_overlay.sh
│   └── rollback_overlay.sh
├── tests/
│   └── test_routing_cases.md
└── logs/
```

Codex should run from:

```bash
cd "/Users/rl_home/Documents/Codex/Hermes_Agent/overlays/codex-delegate"
codex
```

Codex should **not** normally run from:

```bash
cd "/Users/rl_home/.hermes/hermes-agent"
codex
```

Running Codex inside the live repo is only allowed for explicit, approved upgrade/merge work.

---

## 3. Project AGENTS.md Requirements

Create:

```text
/Users/rl_home/Documents/Codex/Hermes_Agent/overlays/codex-delegate/AGENTS.md
```

Recommended content:

```markdown
# AGENTS.md — Hermes Codex Delegate Overlay

## Primary Rules

- Hermes remains the main agent, gateway, memory owner, and skills owner.
- Codex is only a delegated executor for complex coding, debugging, refactoring, automation, and multi-file analysis.
- Do not replace Hermes with Codex.
- Do not modify Hermes core source code.
- Do not modify `/Users/rl_home/.hermes/hermes-agent` unless explicitly approved.
- Do not modify launchd plist, symlinks, venv, or live gateway unless explicitly approved.
- All new tools, policies, wrappers, prompts, docs, tests, and logs must remain in this overlay project unless approved.

## Live Hermes Repo

Live repo:
`/Users/rl_home/.hermes/hermes-agent`

- `main` must remain a clean official upstream mirror.
- `richard/hermes-local` stores local runtime modifications.
- Always inspect `docs/HERMES_LOCAL_GIT_WORKFLOW.md` before proposing live repo changes.
- Always run `git status` before any proposed live repo change.

## Memory Rules

- Codex must not directly write to GBrain raw database.
- Codex must not directly write to Obsidian canonical notes.
- Codex must not directly create or modify Hermes skills.
- Codex may only return Task Summary, Memory Candidate, and Skill Candidate.
- Hermes decides whether a candidate becomes memory or a skill.
- Approved memory must pass through the existing Hermes → GBrain ingest → Obsidian persistence pipeline.

## Token and API Rules

- Prefer Codex CLI ChatGPT sign-in entitlement.
- Do not enable OpenAI API by default.
- Do not assume `OPENAI_API_KEY` is available.
- Do not export `OPENAI_API_KEY` into Hermes default environment.
- If Codex ChatGPT quota is exhausted, request one-time approval before API fallback.
- API fallback is forbidden for private or secret tasks.

## Safety

- Default mode is inspect/dry-run.
- Generate a plan before writing files.
- Generate rollback steps for every applied change.
- Log route decisions without storing sensitive raw content.
```

---

## 4. Responsibility Model

### 4.1 Hermes responsibilities

Hermes remains responsible for:

```text
- WeChat / Telegram / Web / Voice entry points
- Main agent dialogue
- User authentication and gateway behavior
- Local routing decision
- Local memory ownership
- Long-term skills ownership
- GBrain ingest decisions
- Obsidian persistence through existing pipeline
- Result delivery back to the user
```

### 4.2 Local models

Keep 2B, 4B, and 9B models. Do not collapse everything into 9B.

```text
2B = background helper
- title generation
- lightweight classification
- short summaries
- log compression
- memory tagging

4B = normal Hermes front-desk model
- ordinary chat
- rewrite / translation
- simple explanation
- short email drafts
- low-risk triage

9B = local private reasoner and router
- privacy classification
- complexity classification
- decision whether Codex is needed
- GBrain/Obsidian retrieved-context summarization
- private business/project reasoning
```

### 4.3 Codex CLI responsibilities

Codex CLI is only for:

```text
- complex coding tasks
- multi-file analysis
- debugging
- refactoring
- generating scripts
- Power BI / Power Query / Python automation
- repo-level engineering tasks
```

Codex must not become:

```text
- first-level router
- main agent
- primary memory owner
- Telegram/WeChat gateway
- direct GBrain writer
- direct Obsidian writer
- direct Hermes skills writer
```

---

## 5. Routing Policy

First-level routing must be local and Hermes-controlled.

```text
User message
  ↓
Hermes
  ↓
2B / 4B / 9B local routing
  ↓
Hermes handles locally OR delegates to Codex
```

Do not do:

```text
User message
  ↓
Codex decides whether Hermes/local model should handle it
```

### 5.1 Default route table

| Task type | Default route | Codex allowed? |
|---|---|---|
| Ordinary chat | Hermes + 4B | No |
| Rewrite / translate | Hermes + 4B | No |
| Title / tags / compression | Hermes + 2B | No |
| Customer/project/private discussion | Hermes + 9B | Only local Codex if explicitly required |
| GBrain / Obsidian memory query | Hermes + 9B | No cloud fallback |
| Complex non-private code | Codex CLI ChatGPT profile | Yes |
| Complex private code | Local Hermes 9B or local Codex profile | No cloud fallback |
| Secret content | Block | No |

---

## 6. Privacy Policy

Classify each request as one of:

```text
public
private
secret
```

### 6.1 Private indicators

Treat as private by default if it includes:

```text
- customer names
- quotes / quotation / invoice / commercial terms
- contract / NDA
- Gmail / email / calendar
- GBrain / Obsidian memory
- family information
- health information
- company internal project
- local file paths containing personal or business data
```

### 6.2 Secret indicators

Block and do not send to any model if it includes:

```text
- password
- API key
- secret key
- private key
- recovery code
- token
- credential
```

Response should instruct the user to store secrets in a password manager or secret vault.

### 6.3 Cloud fallback rule

```text
public + complex engineering task = Codex ChatGPT allowed
public + quota exhausted = may request API fallback approval
private = local only unless manually redacted and approved
secret = blocked
```

---

## 7. Codex Token and Auth Policy

### 7.1 Priority order

```text
1. Hermes local models: 2B / 4B / 9B
2. Codex CLI using ChatGPT sign-in entitlement
3. Local Codex profile using local oMLX provider, if configured
4. OpenAI API fallback only after one-time user approval
```

### 7.2 OpenAI API default state

OpenAI API must be off by default.

Do not:

```bash
export OPENAI_API_KEY=...
hermes start
```

Do not store API keys in:

```text
- Hermes config
- overlay repo
- AGENTS.md
- logs
- Obsidian
- GBrain
```

### 7.3 Required auth inspection

Before integrating Codex, inspect and report:

```bash
codex --version
codex auth status || true
printenv | grep -E 'OPENAI|CODEX' || true
ls -la ~/.codex || true
```

Do not print secrets. If sensitive values exist, only report that they exist.

### 7.4 API approval

If Codex ChatGPT quota appears exhausted, return a need-approval status to Hermes:

```text
Codex ChatGPT quota appears exhausted.
This task is non-private.
Do you approve using OpenAI API for this task only?
```

Only accept one-time approval tied to:

```text
- task hash
- timestamp
- TTL, recommended 15 minutes
- non-private classification
```

API approval must not be reusable for future tasks.

---

## 8. Codex Config Guidance

Codex user config is expected under:

```text
~/.codex/config.toml
```

Before writing config:

```text
- inspect existing config
- back it up
- do not overwrite unknown settings
- verify current Codex version
- use only supported syntax for installed Codex version
```

Suggested logical profiles:

```text
chatgpt_codex = ChatGPT sign-in entitlement profile
local_private_coder = local oMLX profile for private/local fallback
api_paid = OpenAI API fallback profile, disabled unless one-time approved
```

Do not assume exact profile TOML format without validating installed Codex CLI behavior.

Codex config/profile semantics may vary by version; inspect official config docs and the installed CLI before applying.

Current local oMLX Codex profile decision:

```toml
model = "Qwen3.5-9B-OptiQ-4bit"
model_provider = "localmlx"

[model_providers.localmlx]
name = "Local oMLX"
base_url = "http://127.0.0.1:8000/v1"
env_key = "OMLX_API_KEY"
wire_api = "responses"
```

Do not use `wire_api = "chat"` with the current installed Codex CLI. Keep this profile isolated in `~/.codex/local_private_coder.config.toml` and do not switch the global Codex default provider to `localmlx`.

---

## 9. Wrapper Design: codex_delegate.py

Create:

```text
/Users/rl_home/Documents/Codex/Hermes_Agent/overlays/codex-delegate/tools/codex_delegate.py
```

Wrapper responsibilities:

```text
1. Receive structured Context Pack from Hermes
2. Validate privacy classification
3. Default to Codex ChatGPT profile for allowed complex public engineering tasks
4. Default private Codex delegation to `local_private_coder`
5. Strip OPENAI_API_KEY from environment unless one-time approved API fallback is active
6. Detect quota/rate-limit errors
7. Return need_api_approval rather than auto-switching public tasks to paid API
8. For private tasks, block cloud/API fallback and use local Codex only when delegated
9. Enforce timeout and output size limits
10. Return structured Task Summary / Memory Candidate / Skill Candidate
11. Log non-sensitive audit metadata
```

### 9.1 Required statuses

Wrapper should return one of:

```text
ok
failed
blocked_secret
blocked_private_cloud
need_api_approval
need_manual_codex_intervention
timeout
quota_exhausted_private_no_fallback
```

### 9.2 Quota/rate-limit patterns

Detect, case-insensitive:

```text
rate limit
quota
usage limit
credits
too many requests
insufficient_quota
billing
```

### 9.3 Environment handling

Default behavior:

```python
if not api_fallback_approved:
    env.pop("OPENAI_API_KEY", None)
```

Never log API key values.

---

## 10. Context Pack Schema

Hermes should pass a Context Pack to Codex, not only the last user sentence.

Recommended schema:

```yaml
task_id: "..."
task_hash: "..."
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
output_required:
  - final_answer
  - task_summary
  - memory_candidate
  - skill_candidate
```

---

## 11. Task Summary and Memory Candidate Schema

Codex must return:

```text
Task Summary
- User goal:
- Route used:
- Provider used:
- Files read:
- Files changed:
- Commands executed:
- Key decisions:
- Errors:
- Follow-up actions:

Memory Candidate
- Should store: yes/no
- Memory type: project_fact / workflow / preference / temporary_log / issue / none
- Confidence: high / medium / low
- Suggested GBrain ingest: yes/no
- Suggested Obsidian persistence: yes/no
- Suggested note title:
- Suggested memory text:
- Expiry or review date:
- Do not store:

Skill Candidate
- Should create/update skill: yes/no
- Skill ID:
- Existing skill matched:
- Proposed change:
- Reason:
- Risk:
```

Important:

```text
Codex output is not memory by default.
Codex output is candidate material only.
Hermes decides what becomes memory or skill.
```

---

## 12. Correct Memory Governance for This Environment

Do **not** use the rule “Obsidian first, then GBrain.”

That does not match the current architecture.

Correct rule:

```text
Codex
  ↓
Task Summary / Memory Candidate / Skill Candidate
  ↓
Hermes reviews
  ↓
Hermes decides whether to send candidate into GBrain ingest
  ↓
GBrain processes / embeds / classifies / manages memory
  ↓
Existing GBrain/Obsidian pipeline persists or reflects into Obsidian
```

Canonical governance statement:

```text
Hermes remains the memory and skills owner.
GBrain remains the official ingest and memory processing layer.
Obsidian remains the final human-readable, auditable knowledge store.
Codex must not directly write to GBrain raw database, Obsidian canonical notes, or Hermes skills.
```

Avoid:

```text
Codex → GBrain raw DB
Codex → Obsidian notes
Codex → Hermes skills
```

Use only:

```text
Codex → Hermes review → GBrain ingest → Obsidian persistence
```

---

## 13. Live Repo Change Policy

Live Hermes repo:

```text
/Users/rl_home/.hermes/hermes-agent
```

### 13.1 Default allowed

Codex may inspect:

```bash
cd /Users/rl_home/.hermes/hermes-agent
git status
git branch --show-current
git remote -v
cat docs/HERMES_LOCAL_GIT_WORKFLOW.md
```

### 13.2 Requires explicit approval

```text
- modifying files in live repo
- changing branch
- merging upstream
- restarting gateway
- modifying launchd plist
- changing symlinks
- installing plugin into ~/.hermes/plugins
```

### 13.3 Forbidden by default

```text
- modifying main branch
- editing venv contents
- writing to GBrain raw database
- editing Obsidian canonical notes
- enabling OpenAI API by default
- storing secrets
```

---

## 14. Dry-Run First Workflow

Codex must follow this sequence:

### Phase 1 — Inspect only

```text
- identify current directory
- inspect overlay structure
- inspect live Hermes repo status
- inspect Codex version/auth/config state
- inspect gateway health if safe
- inspect plugin paths
- do not modify files
```

### Phase 2 — Plan

Output:

```text
- proposed files to create
- proposed files to modify
- proposed install location
- rollback plan
- privacy risks
- token/API risks
- memory governance impact
```

### Phase 3 — Apply only after approval

Allowed actions after approval:

```text
- create overlay files
- create wrapper
- create policies
- create tests
- optionally install plugin into ~/.hermes/plugins/codex-delegate
```

### Phase 4 — Validate

Run validation without exposing secrets.

### Phase 5 — Rollback

Provide exact rollback commands.

---

## 15. Install Strategy

Development source:

```text
/Users/rl_home/Documents/Codex/Hermes_Agent/overlays/codex-delegate
```

Runtime plugin location:

```text
/Users/rl_home/.hermes/plugins/codex-delegate
```

Recommended install script behavior:

```text
1. Check source exists
2. Check live Hermes health before install
3. Backup existing ~/.hermes/plugins/codex-delegate if present
4. Symlink or copy overlay into plugin location
5. Do not modify Hermes core
6. Do not restart gateway unless explicitly approved
7. Provide rollback command
```

Prefer symlink during development:

```bash
ln -sfn "/Users/rl_home/Documents/Codex/Hermes_Agent/overlays/codex-delegate" "/Users/rl_home/.hermes/plugins/codex-delegate"
```

Only do this after explicit approval.

---

## 16. Audit Logs

Create logs under:

```text
/Users/rl_home/Documents/Codex/Hermes_Agent/overlays/codex-delegate/logs
```

Recommended JSONL files:

```text
router_decision.jsonl
codex_delegate.jsonl
api_approval.jsonl
memory_candidate.jsonl
tool_calls.jsonl
```

Do not store raw secrets or full private content.

Recommended audit event:

```json
{
  "timestamp": "2026-05-30T00:00:00+10:00",
  "task_hash": "sha256:...",
  "privacy_level": "public|private|secret",
  "route": "local_4b|local_9b|codex_chatgpt|local_codex|api_paid|blocked",
  "api_fallback_requested": false,
  "api_fallback_approved": false,
  "files_changed": [],
  "memory_candidate_generated": true,
  "status": "ok"
}
```

---

## 17. Test Matrix

Codex must create tests or a manual validation checklist covering:

| Test | Expected result |
|---|---|
| Ordinary rewrite | Hermes + 4B, no Codex |
| Translation | Hermes + 4B, no Codex |
| Log summary/title | Hermes + 2B |
| Customer quotation task | Hermes + 9B, private, no cloud fallback |
| GBrain memory query | Hermes + 9B / GBrain, no cloud fallback |
| Secret/token input | blocked, no model call |
| Complex non-private repo task | Codex ChatGPT profile |
| Codex quota exhausted | need_api_approval status |
| API approval | one-time only, non-private only |
| Private task quota exhausted | blocked private cloud fallback |
| Codex completed task | Task Summary + Memory Candidate returned |
| Memory candidate | Hermes review required before GBrain ingest |
| Install overlay | no Hermes core modification |
| Rollback | plugin removed/restored, live repo unchanged |
| Gateway health | remains ok after install |

---

## 18. Rollback Requirements

Every applied change must include rollback.

Rollback should support:

```text
- removing ~/.hermes/plugins/codex-delegate symlink or copy
- restoring prior plugin backup
- restoring prior ~/.codex/config.toml backup if modified
- leaving live Hermes repo unchanged
- checking gateway health
```

Suggested rollback skeleton:

```bash
#!/usr/bin/env bash
set -euo pipefail

PLUGIN="/Users/rl_home/.hermes/plugins/codex-delegate"
BACKUP_DIR="/Users/rl_home/.hermes/backups"

if [ -L "$PLUGIN" ] || [ -d "$PLUGIN" ]; then
  rm -rf "$PLUGIN"
fi

curl -s http://127.0.0.1:8642/health || true
```

---

## 19. Commands for Initial Setup

Create overlay directories:

```bash
mkdir -p "/Users/rl_home/Documents/Codex/Hermes_Agent/overlays/codex-delegate"/{docs,tools,configs,policies,prompts,scripts,tests,logs}
```

Copy this guide into:

```text
/Users/rl_home/Documents/Codex/Hermes_Agent/overlays/codex-delegate/docs/codex_hermes_end_to_end_optimization_guide.md
```

Start Codex from the overlay:

```bash
cd "/Users/rl_home/Documents/Codex/Hermes_Agent/overlays/codex-delegate"
codex
```

Recommended first prompt to Codex:

```text
Read docs/codex_hermes_end_to_end_optimization_guide.md.
Operate in inspect/dry-run mode only.

Live Hermes repo:
/Users/rl_home/.hermes/hermes-agent

Do not modify live repo, plugins, launchd, symlinks, Codex auth, API settings, GBrain, or Obsidian.

Create an implementation plan for the codex-delegate overlay under this directory.
```

---

## 20. End-State Definition

The optimization is successful only if:

```text
1. Hermes remains the live main agent and gateway
2. Gateway health remains ok
3. No Hermes core source files are modified by default
4. Codex delegate overlay exists in Documents/Codex/Hermes_Agent/overlays/codex-delegate
5. Runtime plugin can be installed under ~/.hermes/plugins/codex-delegate only after approval
6. 2B/4B/9B local routing policy is documented
7. Codex CLI is invoked only for complex engineering tasks
8. ChatGPT Codex entitlement is preferred
9. OpenAI API remains off by default
10. API fallback requires one-time approval and is blocked for private/secret tasks
11. Codex does not directly write GBrain, Obsidian, or Hermes skills
12. Memory candidates flow back to Hermes, then through GBrain ingest, then Obsidian persistence
13. Logs and rollback scripts exist
14. Hermes official upgrade workflow remains intact
```

---

## 21. Key Non-Negotiable Rules

```text
Hermes is the main agent.
Codex is a tool.
Local models route first.
Private stays local.
Secrets never enter models.
ChatGPT Codex entitlement before API.
OpenAI API never auto-enables.
Codex never directly writes long-term memory.
Hermes reviews memory candidates.
GBrain remains ingest/processing.
Obsidian remains final human-readable persistence.
Live Hermes repo remains upgrade-safe.
```
