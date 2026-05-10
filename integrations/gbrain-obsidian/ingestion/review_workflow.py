from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class CommitResult:
    ok: bool
    review_path: str
    final_path: str
    backup_path: str | None = None
    dry_run: bool = True
    reason: str = ""


def safe_commit_review_note(
    review_path: str,
    final_path: str,
    *,
    approved: bool = False,
    dry_run: bool = True,
) -> CommitResult:
    """Copy an approved review note to a final path without deleting the review copy."""
    source = Path(review_path).expanduser().resolve()
    target = Path(final_path).expanduser().resolve()
    if not approved:
        return CommitResult(False, str(source), str(target), dry_run=dry_run, reason="explicit approval required")
    if not source.exists():
        return CommitResult(False, str(source), str(target), dry_run=dry_run, reason="review note does not exist")
    if "Gbrain_Review" not in source.parts:
        return CommitResult(False, str(source), str(target), dry_run=dry_run, reason="source is not in Gbrain_Review")

    backup_path = None
    if target.exists():
        timestamp = datetime.now(timezone.utc).astimezone().strftime("%Y%m%d-%H%M%S")
        backup_path = target.with_suffix(target.suffix + f".bak-{timestamp}")

    if dry_run:
        return CommitResult(True, str(source), str(target), str(backup_path) if backup_path else None, True, "dry run")

    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and backup_path is not None:
        shutil.copy2(target, backup_path)
    shutil.copy2(source, target)
    return CommitResult(True, str(source), str(target), str(backup_path) if backup_path else None, False, "committed")
