# AGENTS.md - Hermes Codex Delegate Overlay

## Primary Rules

- Hermes remains the main agent, gateway, memory owner, and skills owner.
- Codex is only a delegated executor for complex coding, debugging, refactoring, automation, and multi-file analysis.
- Do not replace Hermes with Codex.
- Do not modify Hermes core source code.
- Do not modify `/Users/rl_home/.hermes/hermes-agent` unless explicitly approved.
- Do not modify launchd plist files, symlinks, venv contents, or live gateway state unless explicitly approved.
- All new tools, policies, wrappers, prompts, docs, tests, and logs must remain in this overlay project unless approved.

## Live Hermes Repo

Live repo: `/Users/rl_home/.hermes/hermes-agent`

- `main` must remain a clean official upstream mirror.
- `richard/hermes-local` stores Richard's local runtime modifications.
- Always inspect `docs/HERMES_LOCAL_GIT_WORKFLOW.md` before proposing live repo changes.
- Always run `git status` before any proposed live repo change.

## Memory Rules

- Codex must not directly write to the GBrain raw database.
- Codex must not directly write to Obsidian canonical notes.
- Codex must not directly create or modify Hermes skills.
- Codex may only return Task Summary, Memory Candidate, and Skill Candidate.
- Hermes decides whether a candidate becomes memory or a skill.
- Approved memory must pass through the existing Hermes -> GBrain ingest -> Obsidian persistence pipeline.

## API and Auth Rules

- Prefer Codex CLI ChatGPT sign-in entitlement.
- Do not enable OpenAI API by default.
- Do not assume `OPENAI_API_KEY` is available.
- Do not export `OPENAI_API_KEY` into Hermes default environment.
- If Codex ChatGPT quota is exhausted, request one-time approval before API fallback.
- API fallback is forbidden for private or secret tasks.

## Local Runtime Rules

- Default mode is inspect, dry-run, or candidate generation.
- Generate rollback steps for every applied change.
- Log route decisions without storing sensitive raw content.
- Keep runtime writes inside this overlay unless a separate approval explicitly expands scope.
