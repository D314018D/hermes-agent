# Codex Delegate Overlay End-State Audit

Date: 2026-05-30

## Status

The Codex delegate overlay exists as a source-only project. It is not installed
as a live Hermes runtime plugin and does not modify Hermes core, GBrain raw
storage, Obsidian canonical notes, Hermes skills, Codex auth, or OpenAI API
settings.

## Verified

- Hermes remains the live main agent and gateway.
- Gateway health was verified as `ok` during validation.
- oMLX health was verified as `healthy` during validation.
- The overlay exists at `/Users/rl_home/Documents/Codex/Hermes_Agent/overlays/codex-delegate`.
- Routing, privacy, and memory policies are documented under `policies/`.
- Codex delegate wrapper tests pass locally.
- API fallback remains off by default.
- Private and secret task fallback rules are represented in policy and tests.
- Codex output is candidate material only: Task Summary, Memory Candidate, and Skill Candidate.
- Logs and rollback scripts exist.

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
