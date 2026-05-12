# Hermes Local Git Workflow

This document defines how Richard's Mac mini Hermes Agent repo should be managed.

The goal is to allow local custom Hermes changes while still keeping the official Hermes upgrade path clean.

## Current Known Good Live Version

Current live Hermes repo path:

```bash
/Users/rl_home/.hermes/hermes-agent
```

Current live branch:

```bash
richard/hermes-local
```

Current known good live commit:

```bash
8d6db5ea584003786aeb7005a0904218643ce1f9
```

Current Hermes version:

```text
Hermes Agent v0.13.0 (2026.5.7)
```

Current configured default model:

```text
Qwen2.5-7B-Instruct-4bit
```

Current provider:

```text
custom
```

Current health check result:

```json
{"status":"ok","platform":"hermes-agent"}
```

---

## Branch Strategy

Use the following branch model:

```text
origin/main
  = official NousResearch Hermes Agent source

main
  = clean local mirror of official Hermes main

richard/hermes-local
  = Richard's Mac mini running version with local custom changes

myfork/richard/hermes-local
  = Richard's remote backup branch on his own GitHub fork

codex/*
  = temporary Codex working branches
```

## Golden Rule

Never merge local custom code into `main`.

Always keep `main` clean and aligned with official Hermes.

Local custom changes must live in:

```bash
richard/hermes-local
```

---

## Remote Strategy

The official remote should remain:

```bash
origin -> https://github.com/NousResearch/hermes-agent.git
```

Because Richard does not have permission to push to the official repo, add Richard's own fork as a second remote:

```bash
myfork -> https://github.com/<RICHARD_GITHUB_USERNAME>/hermes-agent.git
```

Do not rename or remove `origin`.

---

## First-Time Setup for Richard's Fork

Before running these commands, Richard must create a fork of:

```text
https://github.com/NousResearch/hermes-agent
```

under his own GitHub account.

Then run:

```bash
cd /Users/rl_home/.hermes/hermes-agent

git remote -v
git status
git branch --show-current
```

Add Richard's fork as `myfork`:

```bash
git remote add myfork https://github.com/<RICHARD_GITHUB_USERNAME>/hermes-agent.git
```

Verify remotes:

```bash
git remote -v
```

Expected structure:

```text
origin  https://github.com/NousResearch/hermes-agent.git
myfork  https://github.com/<RICHARD_GITHUB_USERNAME>/hermes-agent.git
```

Push the local running branch to Richard's fork:

```bash
git switch richard/hermes-local
git push -u myfork richard/hermes-local
```

After push, verify:

```bash
git status
git branch -vv
```

---

## Daily Safety Checks

Before making any Git change, always run:

```bash
cd /Users/rl_home/.hermes/hermes-agent

git status
git branch --show-current
git log --oneline --decorate -5
git remote -v
```

If the working tree is not clean, stop and report before continuing.

---

## Safe Official Hermes Upgrade Procedure

Use this process when official Hermes has a new release.

### Step 1: Update Official Mirror

```bash
cd /Users/rl_home/.hermes/hermes-agent

git fetch origin
git switch main
git pull --ff-only origin main
```

`main` must stay clean and only follow official Hermes.

Do not apply Richard's local changes to `main`.

### Step 2: Merge Official Updates Into Local Branch

```bash
git switch richard/hermes-local
git merge main
```

If there are merge conflicts, resolve them carefully.

After resolving conflicts:

```bash
git status
git add <resolved-files>
git commit
```

### Step 3: Test Hermes

Check Git state:

```bash
git status
git log --oneline --decorate -10
```

Check service health:

```bash
curl http://localhost:<PORT>/health
```

Expected response:

```json
{"status":"ok","platform":"hermes-agent"}
```

Also test key local functions:

- Telegram command gateway
- WeChat gateway, if enabled
- Obsidian write
- GBrain retrieval
- local model call
- Apple Notes tools, if enabled
- WebUI, if enabled

### Step 4: Push Updated Local Branch

Only push the local branch to Richard's own fork:

```bash
git push myfork richard/hermes-local
```

Do not push to `origin`.

---

## Creating Temporary Codex Work Branches

For future Codex work, create temporary branches from `richard/hermes-local`:

```bash
git switch richard/hermes-local
git switch -c codex/<task-name>
```

After Codex completes the task, merge the Codex branch back into `richard/hermes-local`:

```bash
git switch richard/hermes-local
git merge --no-ff codex/<task-name>
```

Then test Hermes and push only to `myfork`:

```bash
git push myfork richard/hermes-local
```

Do not merge Codex branches into `main`.

---

## Rollback Procedure

If an upgrade or Codex change breaks Hermes, roll back `richard/hermes-local` to the last known good commit.

Known good commit:

```bash
8d6db5ea584003786aeb7005a0904218643ce1f9
```

Rollback command:

```bash
git switch richard/hermes-local
git reset --hard 8d6db5ea584003786aeb7005a0904218643ce1f9
```

Then restart Hermes only if needed and verify:

```bash
curl http://localhost:<PORT>/health
```

Expected response:

```json
{"status":"ok","platform":"hermes-agent"}
```

After rollback, push the corrected branch to Richard's fork only if Richard approves:

```bash
git push myfork richard/hermes-local --force-with-lease
```

Do not use plain `--force`.

---

## Forbidden Commands

Do not run these unless Richard explicitly approves:

```bash
git push origin main
git push origin richard/hermes-local
git push --force
git reset --hard main
git merge codex/* main
git branch -D richard/hermes-local
git remote remove origin
git remote rename origin upstream
```

---

## Safe Commands

These are generally safe inspection commands:

```bash
git status
git branch --show-current
git branch -vv
git log --oneline --decorate --graph -20
git remote -v
git fetch origin
curl http://localhost:<PORT>/health
```

---

## Summary

Richard's local Hermes repo must follow this rule:

```text
official Hermes updates flow into main
main updates flow into richard/hermes-local
richard/hermes-local is pushed only to myfork
main is never polluted by local custom changes
```

The safe upgrade direction is:

```text
origin/main -> main -> richard/hermes-local -> myfork/richard/hermes-local
```

Never reverse this direction.
