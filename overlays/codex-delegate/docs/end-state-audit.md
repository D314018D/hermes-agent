# Codex Delegate Overlay End-State Audit

Date: 2026-05-30

## Status

The Codex delegate overlay exists as an isolated integration project. After
explicit approval, it is also installed as a Hermes user plugin symlink at
`/Users/rl_home/.hermes/plugins/codex-delegate`. It does not modify Hermes core,
GBrain raw storage, Obsidian canonical notes, Hermes skills, Codex auth, or
OpenAI API settings.

## Verified

- Hermes remains the live main agent and gateway.
- Gateway health was verified as `ok` during validation.
- oMLX health was verified as `healthy` during validation.
- The overlay exists at `/Users/rl_home/Documents/Codex/Hermes_Agent/overlays/codex-delegate`.
- The runtime plugin symlink points to the overlay source.
- The optional Codex profile exists at `/Users/rl_home/.codex/codex-delegate.config.toml`.
- The optional local Codex profile template exists at `configs/local_private_coder.config.toml` and installs to `/Users/rl_home/.codex/local_private_coder.config.toml`.
- Routing, privacy, and memory policies are documented under `policies/`.
- Codex delegate wrapper tests pass locally.
- API fallback remains off by default.
- Private and secret task fallback rules are represented in policy and tests.
- Codex output is candidate material only: Task Summary, Memory Candidate, and Skill Candidate.
- Logs and rollback scripts exist. The wrapper writes JSONL audit metadata for
  delegate events, route decisions, API approval requests, memory candidates,
  and tool calls without raw private content.

## End-State Checklist

| Requirement | Current evidence |
|---|---|
| Hermes remains live main agent and gateway | `curl http://127.0.0.1:8642/health` returns `{"status":"ok","platform":"hermes-agent"}` |
| No Hermes core source modified by this overlay | Runtime integration is a user plugin symlink; overlay source is under `Documents/Codex/Hermes_Agent/overlays` |
| Codex delegate overlay exists | `overlays/codex-delegate` contains wrapper, policies, prompts, scripts, tests, and logs directory |
| Runtime plugin only after approval | Installed after approval at `~/.hermes/plugins/codex-delegate` |
| 2B/4B/9B routing documented | `policies/routing_policy.yaml` |
| Codex only for complex engineering | `policies/routing_policy.yaml` and `tools/codex_delegate.py` scope gate |
| ChatGPT entitlement preferred | `configs/codex-delegate.config.toml` profile and `codex login status` show ChatGPT login |
| Local private Codex profile available | `configs/local_private_coder.config.toml` uses provider `localmlx`, `Qwen3.5-9B-OptiQ-4bit`, `OMLX_API_KEY`, and `wire_api = "responses"` |
| OpenAI API off by default | Profile excludes `OPENAI_API_KEY`; wrapper strips API env unless approved |
| One-time API fallback required | Wrapper returns `need_api_approval`; private fallback returns `quota_exhausted_private_no_fallback` |
| No direct GBrain/Obsidian/skill writes | `AGENTS.md`, policies, prompt, and wrapper response schemas enforce candidate-only output |
| Candidate memory flow preserved | `policies/memory_policy.yaml` and wrapper `memory_candidate` structure |
| Logs and rollback exist | `logs/`, `scripts/rollback_overlay.sh`, and audit JSONL writers |
| Upgrade workflow intact | live repo branch `richard/hermes-local` is clean and separate from official `main` strategy |

## Applied Runtime Item

The live launchd plist previously had a stale `HERMES_OBSIDIAN_GBRAIN_ROOT` value:

```text
/Users/rl_home/Documents/Codex/Hermes Agent/integrations/gbrain-obsidian
```

On 2026-05-30, this was updated to the canonical path:

```text
/Users/rl_home/Documents/Codex/Hermes_Agent/integrations/gbrain-obsidian
```

The applied script was:

```bash
cd /Users/rl_home/Documents/Codex/Hermes_Agent/overlays/codex-delegate
./scripts/fix_launchd_gbrain_path.sh
```

Backup created:

```text
/Users/rl_home/.hermes/backups/ai.hermes.gateway.plist.20260530-202610.bak
```

Hermes gateway was restarted and verified with:

```bash
curl -sS http://127.0.0.1:8642/health
/Users/rl_home/.local/bin/hermes plugins list
```

## Rollback

The path-fix script writes a timestamped backup under `/Users/rl_home/.hermes/backups`.
Rollback is restoring that plist backup, restarting the Hermes gateway, and
checking gateway health.
