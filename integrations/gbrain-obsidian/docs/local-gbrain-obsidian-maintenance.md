# Local GBrain Obsidian Maintenance

## Reason

This adds a low-resource Obsidian helper layer for the local Hermes + oMLX + GBrain setup. GBrain remains the memory, embedding, index, query, and graph layer. These scripts only prepare human-readable Obsidian notes, MOC pages, and backlink reports.

## Files Changed

- GBrain config: `sync.repo_path` set to `/Users/rl_home/Documents/Codex/Hermes_Agent/integrations/gbrain-obsidian/obsidian-vault`
- `scripts/gbrain_obsidian/common.py`
- `scripts/gbrain_obsidian/process_review.py`
- `scripts/gbrain_obsidian/route_staging.py`
- `scripts/gbrain_obsidian/update_mocs.py`
- `scripts/gbrain_obsidian/check_backlinks.py`
- `scripts/gbrain_obsidian/dedupe_existing_notes.py`
- `scripts/gbrain_obsidian/run_gbrain_extract.py`
- `scripts/gbrain_obsidian/run_maintenance.sh`
- `logs/gbrain_obsidian/.gitkeep`

## Usage

Dry run:

```bash
scripts/gbrain_obsidian/run_maintenance.sh --dry-run
```

Write:

```bash
scripts/gbrain_obsidian/run_maintenance.sh --write
```

Optional limit:

```bash
scripts/gbrain_obsidian/run_maintenance.sh --dry-run --limit 20
```

## Resource Protection

- Default mode is dry-run.
- Write mode refuses to write if free disk space is below 10GB.
- Markdown files over 1MB are skipped.
- Each run processes at most `--limit` files per stage by default.
- System helper outputs such as `gbrain-backlink-report.md` are skipped by the staging router.
- Review notes are skipped when the same `content_hash` or `source_file` already exists in staging or a formal note folder.
- The staging router skips notes that were already routed into a formal note folder.
- MOC updates scan formal note folders only; staging notes and system reports are not used as MOC sources.
- Backlink checks ignore system reports and attachment-style links such as `attachments/...`.
- Existing helper duplicates can be cleaned with `dedupe_existing_notes.py`; it moves duplicate staging notes to `00_Inbox/Gbrain_Staging/_deduped/` and only moves exact duplicate formal notes to `00_Inbox/Processed/_deduped_formal/`.
- GBrain extract commands are serialized through `/Users/rl_home/.gbrain/hermes-gbrain.lock`.
- If another GBrain embed or maintenance process appears to be running, the GBrain command is skipped.
- The scripts do not schedule cron jobs.

## Upgrade Impact

Low. These are local helper scripts under the Hermes `gbrain-obsidian` integration and do not modify upstream GBrain, Hermes, oMLX, or Obsidian plugin code.

## Rollback

Delete `scripts/gbrain_obsidian/`, `logs/gbrain_obsidian/`, and this document. To roll back the GBrain path setting, clear or replace `sync.repo_path` with `gbrain config set sync.repo_path <previous-path>`. No database migration or service restart is required.
