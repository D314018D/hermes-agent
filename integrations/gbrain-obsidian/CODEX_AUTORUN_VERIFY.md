# CODEX_AUTORUN_VERIFY.md

## Mission

Upgrade the existing `hermes-gbrain-obsidian-starter` project so it follows a GBrain-style flow:

```text
input signal
→ deterministic collector
→ Hermes / ingestion judgment
→ canonical brain page update
→ Compiled Truth + append-only Timeline
→ Obsidian Vault / Markdown Brain Repo
→ optional GBrain import/embed/extract/query verification
```

This file is designed for Codex to read, implement, run, and verify automatically.

---

## Safety Rules

1. Keep everything local-first.
2. Do not permanently delete files.
3. Do not require GBrain to be installed for the core ingestion test to pass.
4. If GBrain is not installed, skip GBrain verification and write `GBRAIN_SKIPPED` in the report.
5. If no API keys exist, skip embedding-dependent verification and write why.
6. Never store raw content by default unless `SAVE_RAW_CONTENT=true`.
7. Preserve append-only timeline evidence.
8. Do not create duplicate canonical pages for the same project.

---

## Official GBrain Command Assumptions

Use these commands only if `gbrain` is available on PATH:

```bash
gbrain --version
gbrain doctor --json
gbrain import <brain_repo_or_vault_path> --no-embed
gbrain embed --stale
gbrain search "meeting" --limit 3
gbrain query "What is the status of Woolworths N70 Robot Test Unit?"
gbrain extract links --source db --dry-run
gbrain extract links --source db
gbrain extract timeline --source db
gbrain stats
```

If a command fails, do not crash the whole verification. Capture the error in `verification_report.md`.

---

## Required New Files

Create or update these files:

```text
agents/brain-first-policy.md
config/brain_schema.yaml
config/entity_aliases.yaml
ingestion/page_resolver.py
ingestion/citation_builder.py
ingestion/timeline_appender.py
ingestion/truth_compiler.py
ingestion/brain_page_writer.py
maintenance/gbrain_sync.py
maintenance/gbrain_maintain.py
maintenance/vault_cleaner.py
scripts/gbrain_query.py
scripts/nightly_maintain.py
scripts/vault_clean.py
connectors/voice/example_wechat_woolworths_n70.json
tests/test_page_resolver.py
tests/test_timeline_appender.py
tests/test_pipeline_voice.py
scripts/autoverify.py
```

---

## Required Configuration

Create `config/brain_schema.yaml`:

```yaml
canonical_page_types:
  project:
    directory: "03-projects"
    required_sections:
      - "Compiled Truth"
      - "Current Status"
      - "Timeline"
      - "References"
  person:
    directory: "01-people"
    required_sections:
      - "Compiled Truth"
      - "Relationships"
      - "Timeline"
      - "References"
  company:
    directory: "02-companies"
    required_sections:
      - "Compiled Truth"
      - "Key Contacts"
      - "Projects"
      - "Timeline"
      - "References"
  decision:
    directory: "05-decisions"
    required_sections:
      - "Decision"
      - "Reason"
      - "Impact"
      - "Timeline"
      - "References"
  meeting:
    directory: "04-meetings"
    required_sections:
      - "Summary"
      - "Attendees"
      - "Actions"
      - "Timeline"
      - "References"

timeline:
  append_only: true
  date_heading_format: "YYYY-MM-DD"
  require_source: true

compiled_truth:
  max_length_chars: 1200
  update_policy: "rewrite_from_existing_truth_plus_new_evidence"
```

Create `config/entity_aliases.yaml`:

```yaml
companies:
  Woolworths:
    aliases:
      - Woolies
      - WWS
      - Woolworths Australia
  Hanshow:
    aliases:
      - Hanshow Technology
      - Hanshow Australia

projects:
  Woolworths N70 Robot Test Unit:
    aliases:
      - N70 robot
      - large robot test unit
      - robot test unit
      - Woolworths robot pilot
      - Woolworths N70

people:
  Ben:
    aliases:
      - Ben from Woolworths
  Travis:
    aliases:
      - Travis from Woolworths
```

---

## Implementation Requirements

### 1. `ingestion/page_resolver.py`

Purpose: resolve input into a canonical brain page.

Required return shape:

```python
from dataclasses import dataclass

@dataclass
class PageResolution:
    target_type: str
    target_title: str
    target_path: str
    confidence: float
    reason: str
```

Rules:

- If content mentions `N70` and `Woolworths`, route to:
  `obsidian-vault/03-projects/woolworths-n70-robot-test-unit.md`
- If content has a known project alias, use that project page.
- If content has project keywords and a company entity, create/update a project page.
- If confidence is low, route to `00-inbox` and mark `needs_review: true`.

### 2. `ingestion/citation_builder.py`

Build source attribution for every timeline entry.

For voice input, include:

- source_type
- source_app
- captured_at
- attachment links

Example output:

```text
source_type=voice; source_app=wechat; captured_at=2026-04-25T14:30:00+10:00; attachments=[[attachments/2026/04/2026-04-25-wechat-woolworths-n70.m4a]]
```

### 3. `ingestion/timeline_appender.py`

Implement append-only behavior.

Rules:

- If `## Timeline` does not exist, create it.
- Append under `### YYYY-MM-DD — source_app/source_type`.
- Do not rewrite older entries.
- Include source attribution.
- Add concise evidence bullets.

### 4. `ingestion/truth_compiler.py`

MVP deterministic behavior:

- Combine existing truth + new summary.
- Remove duplicate sentences.
- Keep under 1200 chars.
- Do not invent facts.
- Later this can be replaced by Hermes/LLM judgment.

### 5. `ingestion/brain_page_writer.py`

Behavior:

- If target page does not exist, create canonical page with YAML frontmatter and required sections.
- If target page exists:
  - update `## Compiled Truth`
  - append to `## Timeline`
  - preserve existing content
- Add/update frontmatter:
  - type
  - title
  - entities
  - tags
  - updated_at
- Do not delete old timeline evidence.

### 6. Upgrade `ingestion/pipeline.py`

New pipeline:

```text
score
→ classify
→ summarize
→ extract entities
→ should_store?
→ resolve canonical page
→ build citation
→ write/update brain page
→ optional gbrain sync
```

Behavior:

- If `GBRAIN_ENABLED=false`, ingestion must still work.
- If `GBRAIN_ENABLED=true`, try GBrain sync but do not crash if it fails.
- If score is low, do not store unless `STORE_LOW_VALUE_TO_INBOX=true`.

---

## Test Input

Create `connectors/voice/example_wechat_woolworths_n70.json`:

```json
{
  "source_type": "voice",
  "source_app": "wechat",
  "captured_at": "2026-04-25T14:30:00+10:00",
  "title": "Woolworths N70 robot test unit follow-up",
  "content": "今天和 Woolworths Ben 沟通了，客户希望尽快拿到 N70 大机器人测试机，澳洲认证周期预计 7-8 周，下一步要确认总部发货时间。",
  "attachments": [
    "2026/04/2026-04-25-wechat-woolworths-n70.m4a"
  ],
  "metadata": {
    "sender": "Richard",
    "channel": "wechat",
    "language": "zh-CN"
  }
}
```

Expected output page:

```text
obsidian-vault/03-projects/woolworths-n70-robot-test-unit.md
```

Expected page sections:

```text
---
frontmatter
---

# Woolworths N70 Robot Test Unit

## Compiled Truth

## Current Status

## Timeline

### 2026-04-25 — wechat/voice

Source: ...

- ...

## References
```

---

## Required Tests

Implement pytest tests.

### `tests/test_page_resolver.py`

Assert that N70 + Woolworths input resolves to:

```text
03-projects/woolworths-n70-robot-test-unit.md
```

### `tests/test_timeline_appender.py`

Assert:

- existing timeline entries remain
- new entry is appended
- source attribution is present

### `tests/test_pipeline_voice.py`

Run the full pipeline using the voice example.

Assert:

- page exists
- contains `## Compiled Truth`
- contains `## Timeline`
- contains `2026-04-25`
- contains `Woolworths`
- contains `N70`
- contains audio attachment reference

---

## Auto-Run Verification Script

Create `scripts/autoverify.py`.

It must:

1. Print environment info:
   - Python version
   - working directory
   - whether `gbrain` exists
2. Set safe env vars:
   - `OBSIDIAN_VAULT_PATH=./obsidian-vault`
   - `MIN_STORE_SCORE=3`
   - `SAVE_RAW_CONTENT=false`
   - `GBRAIN_ENABLED=false` for core test
3. Run:
   ```bash
   python scripts/ingest.py connectors/voice/example_wechat_woolworths_n70.json
   ```
4. Check expected page exists.
5. Inspect expected page content.
6. Run pytest if available:
   ```bash
   python -m pytest tests -q
   ```
   If pytest is not installed, write `PYTEST_SKIPPED`.
7. If `gbrain` exists:
   - run `gbrain --version`
   - run `gbrain doctor --json`
   - run `gbrain import ./obsidian-vault --no-embed`
   - run `gbrain embed --stale`
   - run `gbrain search "Woolworths N70" --limit 3`
   - run `gbrain query "What is the status of Woolworths N70 Robot Test Unit?"`
   - run `gbrain extract links --source db --dry-run`
   - run `gbrain stats`
8. Write `verification_report.md`.

The script should never crash on optional GBrain failure. It should record pass/fail/skip for each step.

---

## `scripts/autoverify.py` Minimal Template

Use this as a starting point:

```python
#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "verification_report.md"

def run(cmd, env=None, optional=False):
    try:
        result = subprocess.run(
            cmd,
            cwd=ROOT,
            env=env or os.environ.copy(),
            text=True,
            capture_output=True,
            check=False,
        )
        return {
            "cmd": " ".join(cmd),
            "returncode": result.returncode,
            "stdout": result.stdout[-4000:],
            "stderr": result.stderr[-4000:],
            "ok": result.returncode == 0,
            "optional": optional,
        }
    except Exception as e:
        return {
            "cmd": " ".join(cmd),
            "returncode": -1,
            "stdout": "",
            "stderr": str(e),
            "ok": False,
            "optional": optional,
        }

def main():
    results = []
    env = os.environ.copy()
    env["OBSIDIAN_VAULT_PATH"] = "./obsidian-vault"
    env["MIN_STORE_SCORE"] = "3"
    env["SAVE_RAW_CONTENT"] = "false"
    env["GBRAIN_ENABLED"] = "false"

    expected_page = ROOT / "obsidian-vault/03-projects/woolworths-n70-robot-test-unit.md"

    results.append({
        "cmd": "environment",
        "returncode": 0,
        "stdout": f"Python={sys.version}\nROOT={ROOT}\ngbrain={shutil.which('gbrain')}",
        "stderr": "",
        "ok": True,
        "optional": False,
    })

    results.append(run([
        sys.executable,
        "scripts/ingest.py",
        "connectors/voice/example_wechat_woolworths_n70.json"
    ], env=env))

    content_checks = []
    if expected_page.exists():
        txt = expected_page.read_text(encoding="utf-8")
        for needle in [
            "## Compiled Truth",
            "## Timeline",
            "2026-04-25",
            "Woolworths",
            "N70",
            "2026-04-25-wechat-woolworths-n70.m4a",
        ]:
            content_checks.append((needle, needle in txt))
    else:
        content_checks.append((str(expected_page), False))

    results.append({
        "cmd": "content checks",
        "returncode": 0 if all(ok for _, ok in content_checks) else 1,
        "stdout": "\n".join([f"{'PASS' if ok else 'FAIL'} {needle}" for needle, ok in content_checks]),
        "stderr": "",
        "ok": all(ok for _, ok in content_checks),
        "optional": False,
    })

    if shutil.which("pytest"):
        results.append(run([sys.executable, "-m", "pytest", "tests", "-q"], env=env))
    else:
        results.append({
            "cmd": "pytest",
            "returncode": 0,
            "stdout": "PYTEST_SKIPPED: pytest not installed",
            "stderr": "",
            "ok": True,
            "optional": True,
        })

    if shutil.which("gbrain"):
        gbrain_cmds = [
            ["gbrain", "--version"],
            ["gbrain", "doctor", "--json"],
            ["gbrain", "import", "./obsidian-vault", "--no-embed"],
            ["gbrain", "embed", "--stale"],
            ["gbrain", "search", "Woolworths N70", "--limit", "3"],
            ["gbrain", "query", "What is the status of Woolworths N70 Robot Test Unit?"],
            ["gbrain", "extract", "links", "--source", "db", "--dry-run"],
            ["gbrain", "stats"],
        ]
        for cmd in gbrain_cmds:
            results.append(run(cmd, env=env, optional=True))
    else:
        results.append({
            "cmd": "gbrain optional verification",
            "returncode": 0,
            "stdout": "GBRAIN_SKIPPED: gbrain not found on PATH",
            "stderr": "",
            "ok": True,
            "optional": True,
        })

    lines = [
        "# Verification Report",
        "",
        f"Generated: {datetime.now().isoformat()}",
        "",
    ]

    hard_failures = []
    for r in results:
        status = "PASS" if r["ok"] else ("WARN" if r["optional"] else "FAIL")
        if not r["ok"] and not r["optional"]:
            hard_failures.append(r["cmd"])
        lines.extend([
            f"## {status}: `{r['cmd']}`",
            "",
            f"Return code: `{r['returncode']}`",
            "",
            "### STDOUT",
            "```",
            r["stdout"],
            "```",
            "",
            "### STDERR",
            "```",
            r["stderr"],
            "```",
            "",
        ])

    lines.append("## Final Result")
    if hard_failures:
        lines.append("FAIL")
        lines.append("")
        lines.append("Hard failures:")
        for f in hard_failures:
            lines.append(f"- {f}")
    else:
        lines.append("PASS")

    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(REPORT)
    return 1 if hard_failures else 0

if __name__ == "__main__":
    raise SystemExit(main())
```

---

## Final Codex Instruction

After implementing the upgrade, run:

```bash
python scripts/autoverify.py
```

Then open:

```text
verification_report.md
```

If hard failures exist, fix them and rerun until the final result is `PASS`.

Do not stop after writing files. You must run the verification script and report what passed, failed, or was skipped.
