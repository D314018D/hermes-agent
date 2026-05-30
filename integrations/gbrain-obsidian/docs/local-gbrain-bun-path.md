# Local GBrain Bun PATH Fix

Date: 2026-05-18

## Reason

Hermes Weixin-triggered GBrain sync failed with `env: bun: No such file or directory`. The interactive shell has Bun at `/Users/rl_home/.local/bin/bun`, but launchd/Hermes may run with a narrower PATH. The installed `gbrain` executable uses `#!/usr/bin/env bun`, so it fails unless Bun is discoverable in the child process PATH.

## Files Changed

- `integrations/gbrain-obsidian/maintenance/gbrain_cli.py`
- `integrations/gbrain-obsidian/docs/local-gbrain-bun-path.md`

## Upgrade Impact

This is isolated to the local Hermes Obsidian/GBrain integration. It does not modify GBrain official source code or global Bun installation. The helper now resolves Bun from known local locations and passes a PATH containing Bun only to GBrain subprocesses.

## Rollback

Restore `maintenance/gbrain_cli.py` to the previous version, or remove the Bun resolution helpers and the `env=gbrain_env()` subprocess argument. No database or model configuration changes are required.
