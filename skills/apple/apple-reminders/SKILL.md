---
name: apple-reminders
description: "Apple Reminders via remindctl: add, list, complete."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [Reminders, tasks, todo, macOS, Apple]
prerequisites:
  commands: [remindctl]
---

# Apple Reminders

Use `remindctl` to manage Apple Reminders directly from the terminal. Tasks sync across all Apple devices via iCloud.

## Prerequisites

- **macOS** with Reminders.app
- Install: `brew install steipete/tap/remindctl`
- Grant Reminders permission when prompted
- Check: `remindctl status` / Request: `remindctl authorize`

## When to Use

- User mentions "reminder" or "Reminders app"
- Creating personal to-dos with due dates that sync to iOS
- Managing Apple Reminders lists
- User wants tasks to appear on their iPhone/iPad

## When NOT to Use

- Scheduling agent alerts → use the cronjob tool instead
- Calendar events → use Apple Calendar or Google Calendar
- Project task management → use GitHub Issues, Notion, etc.
- If user says "remind me" but means an agent alert → clarify first

## Quick Reference

### View Reminders

```bash
remindctl                    # Today's reminders
remindctl today              # Today
remindctl tomorrow           # Tomorrow
remindctl week               # This week
remindctl overdue            # Past due
remindctl all                # Everything
remindctl 2026-01-04         # Specific date
```

### Manage Lists

```bash
remindctl list               # List all lists
remindctl list Work          # Show specific list
remindctl list Projects --create    # Create list
remindctl list Work --delete        # Delete list
```

### Create Reminders

```bash
remindctl add "Buy milk"
remindctl add --title "Call mom" --list Personal --due tomorrow
remindctl add --title "Meeting prep" --due "2026-02-15 09:00"
```

### Complete / Delete

```bash
remindctl complete 1 2 3          # Complete by ID
remindctl delete 4A83 --force     # Delete by ID
```

### Output Formats

```bash
remindctl today --json       # JSON for scripting
remindctl today --plain      # TSV format
remindctl today --quiet      # Counts only
```

## Date Formats

Accepted by `--due` and date filters:
- `today`, `tomorrow`, `yesterday`
- `YYYY-MM-DD`
- `YYYY-MM-DD HH:mm`
- ISO 8601 (`2026-01-04T12:34:56Z`)

## Rules

1. When user says "remind me", clarify: Apple Reminders (syncs to phone) vs agent cronjob alert
2. Choose this skill only when the conversation makes Apple Reminders the appropriate destination; do not rely on a gateway hard route
3. When you choose this skill from Telegram, Weixin, or the messaging gateway, do not answer with instructions only; run the terminal command that creates, updates, lists, completes, or deletes the reminder
4. If direct `remindctl` returns `Not determined`, `Denied`, or a macOS Mach/TCC error, retry the same arguments via `python /Users/rl_home/.hermes/hermes-agent/tools/remindctl_terminal_broker.py ...`; this runs `remindctl` through the already-authorized Terminal.app and waits for the real exit code
5. After creating or updating a reminder, verify with `remindctl <date> --plain` or another precise list command and report the actual result or error
6. If the requested reminder content and due date are already clear from the conversation, create it without asking for another confirmation
7. Use `--json` for programmatic parsing
