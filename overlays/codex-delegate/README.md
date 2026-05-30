# Hermes Codex Delegate Overlay

This overlay keeps Hermes as the main agent while allowing Hermes to delegate selected complex engineering tasks to Codex.

Codex is not the router, memory owner, skill owner, GBrain writer, or Obsidian writer. It returns structured candidate material for Hermes to review.

## Layout

- `tools/codex_delegate.py` - guarded wrapper for Codex delegation.
- `configs/codex-delegate.config.toml` - optional Codex ChatGPT delegate profile template; not installed by default.
- `configs/local_private_coder.config.toml` - optional isolated local oMLX Codex profile; not installed by default.
- `policies/` - routing, privacy, and memory governance rules.
- `prompts/` - Context Pack and output schemas.
- `scripts/` - read-only inspection, validation, optional plugin install, optional profile install, optional launchd path fix, rollback helper.
- `tests/` - local wrapper tests.
- `logs/` - non-sensitive JSONL audit logs.

## Default Safety Boundary

The overlay source does not edit Hermes core, write GBrain data, write Obsidian notes, or create Hermes skills. Runtime plugin/profile installation is explicit local state and must remain reversible.

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

Install the local/private Codex profile only after confirming oMLX is healthy:

```bash
cd /Users/rl_home/Documents/Codex/Hermes_Agent/overlays/codex-delegate
./scripts/install_profile.sh local_private_coder
```

This writes `~/.codex/local_private_coder.config.toml`, uses `env_key = "OMLX_API_KEY"`, and does not change the global Codex default model.

The plugin installer is also separate:

```bash
cd /Users/rl_home/Documents/Codex/Hermes_Agent/overlays/codex-delegate
./scripts/install_overlay.sh
```

It installs a symlink at `/Users/rl_home/.hermes/plugins/codex-delegate`, backs up any existing target, and does not restart Hermes.
