# Hermes Codex Delegate Overlay

This overlay keeps Hermes as the main agent while allowing Hermes to delegate selected complex engineering tasks to Codex.

Codex is not the router, memory owner, skill owner, GBrain writer, or Obsidian writer. It returns structured candidate material for Hermes to review.

## Layout

- `tools/codex_delegate.py` - guarded wrapper for Codex delegation.
- `configs/codex-delegate.config.toml` - optional Codex profile template; not installed by default.
- `policies/` - routing, privacy, and memory governance rules.
- `prompts/` - Context Pack and output schemas.
- `scripts/` - read-only inspection, validation, optional profile install, optional launchd path fix, rollback helper.
- `tests/` - local wrapper tests.
- `logs/` - non-sensitive JSONL audit logs.

## Default Safety Boundary

The overlay is source-only by default. It does not install a Hermes plugin, edit Hermes core, change launchd, write GBrain data, write Obsidian notes, or modify `~/.codex`.

## Basic Validation

```bash
cd /Users/rl_home/Documents/Codex/Hermes_Agent/overlays/codex-delegate
./scripts/validate_overlay.sh
```

## Read-Only Environment Inspection

```bash
cd /Users/rl_home/Documents/Codex/Hermes_Agent/overlays/codex-delegate
./scripts/inspect_environment.sh
```

## Optional Steps

The profile installer and launchd path fixer are intentionally separate scripts. Review them before running, and run them only after explicit approval for local runtime/config changes.
