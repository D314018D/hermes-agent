---
name: playwright-local
description: Use this skill when Hermes needs reliable local browser automation on macOS. Prefer playwright-cli for routine browser actions and playwright-mcp when an MCP-aware workflow explicitly needs Playwright tools.
version: 1.0.0
author: Codex
license: MIT
metadata:
  hermes:
    tags: [playwright, browser, automation, mcp, local, macos]
    related_skills: [hermes-agent, codex]
---

# Playwright Local

Use this skill when Hermes needs to open pages, click, type, capture screenshots, or inspect browser state with local Playwright instead of heavier desktop control.

## Expected local tools

- `playwright-cli`: `/opt/homebrew/bin/playwright-cli`
- `playwright-mcp`: `/opt/homebrew/bin/playwright-mcp`

If a local wrapper script exists in your environment, it may be convenient for repeated browser actions, but this skill should not depend on a machine-specific wrapper path.

## Decision rule

Prefer `playwright-cli` for:

- opening or reusing a browser session
- navigating stable pages with selectors
- filling forms
- taking snapshots or screenshots on demand
- low-token local browser work

Prefer `playwright-mcp` for:

- workflows that explicitly require MCP tool integration
- structured browser automation from an MCP-aware agent

Prefer desktop automation only when:

- a native macOS dialog is involved
- browser extensions are required
- the task depends on the visible desktop rather than browser DOM control

## Fast commands

```bash
playwright-cli open https://example.com
playwright-cli list
playwright-cli -s=<session> goto https://github.com/login
playwright-cli -s=<session> screenshot
playwright-cli -s=<session> click "text=Sign in"
playwright-cli -s=<session> fill "input[name='login']" "your-user-name"
```

## MCP note

Codex is configured to launch Playwright MCP with:

```toml
[mcp_servers.playwright]
command = "/opt/homebrew/bin/playwright-mcp"
args = []
```

If Hermes needs its own MCP registration later, add the same binary path through Hermes MCP configuration instead of pointing at a remote browser tool.
