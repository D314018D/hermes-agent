---
type: skill
title: "Current Model Routing"
updated_at: "2026-05-06T22:37:01+10:00"
tags:
  - "skill"
  - "text"
entities:
  - "Agent"
  - "Gateway"
  - "Hermes"
  - "Post"
  - "Reboot"
  - "Smoke"
  - "Test"
---

# Current Model Routing

## Compiled Truth
Post-reboot smoke test for Hermes Agent. Gateway, oMLX, API, web search, and ingestion pipeline were checked.

## Current Status
Post-reboot smoke test for Hermes Agent. Gateway, oMLX, API, web search, and ingestion pipeline were checked.

## 2026-05-15 Stability Routing Update

- Main local model: Qwen3.5-4B-OptiQ-4bit via http://127.0.0.1:8000/v1.
- Complex local escalation model: Qwen3.5-9B-OptiQ-4bit.
- Vision model: Qwen3-VL-4B-Instruct-MLX-4bit, on demand.
- Lightweight auxiliary tasks: Qwen3.5-2B-OptiQ-4bit.
- Cloud escalation: gpt-5.4 for high-value coding, architecture, research, and long-context work.
- Local policy: prefer low memory pressure, single-request oMLX scheduling, review-first GBrain/Obsidian ingestion, and explicit escalation for complex tasks.

## Timeline

### 2026-04-25 — wechat/voice

Source: source_type=voice; source_app=wechat; captured_at=2026-04-25T21:30:00+10:00; channel=wechat; language=zh-CN; sender=Richard

- 微信语音记录：现在用的模型被错误记录成 chatgtp 5.4，需要更正为本地规则路由里的 Qwen 和 Hermes 模型配置，并输入到 Obsidian。

### 2026-04-25 — weixin_gateway_hook/text

Source: source_type=text; source_app=weixin_gateway_hook; captured_at=2026-04-25T21:37:07+10:00; chat_id=manual-chat; hook=wechat_obsidian_capture; platform=weixin; session_id=manual-smoke

- 微信请求记录当前模型配置。
- 不要使用会话旧上下文中的自报模型；以下值来自本机 ~/.hermes/config.yaml。
- 主模型 provider: custom；主模型 name: Qwen2.5-7B-Instruct-4bit；主模型 endpoint: http://127.0.0.1:8000/v1。
- STT provider: local；STT local model: base。
- TTS provider: openai；TTS model: Qwen3-TTS-12Hz-0.6B-CustomVoice-8bit；TTS endpoint: http://127.0.0.1:8000/v1。
- 触发消息: 测试，现在你读到的模型是什么？把这条记录进入到obisdian

### 2026-04-25 — weixin_gateway_hook/text

Source: source_type=text; source_app=weixin_gateway_hook; captured_at=2026-04-25T21:43:57+10:00; chat_id=o9cq8025w3PDOEUW448Iz90f0mLU@im.wechat; hook=wechat_obsidian_capture; platform=weixin; session_id=20260425_213928_702c134e

- 微信请求记录当前模型配置。
- 不要使用会话旧上下文中的自报模型；以下值来自本机 ~/.hermes/config.yaml。
- 主模型 provider 是 custom；主模型 name 是 Qwen2.5-7B-Instruct-4bit；主模型 endpoint 是 http://127.0.0.1:8000/v1。
- STT provider 是 local；STT local model 是 base。
- TTS provider 是 openai；TTS model 是 Qwen3-TTS-12Hz-0.6B-CustomVoice-8bit；TTS endpoint 是 http://127.0.0.1:8000/v1。

### 2026-05-03 — hermes/text

Source: source_type=text; source_app=hermes; captured_at=2026-05-03T22:16:46+10:00; ingested_by=obsidian_write_note

- This is a test note created by Hermes to verify Obsidian access.

### 2026-05-05 — codex-smoke-test/text

Source: source_type=text; source_app=codex-smoke-test; captured_at=2026-05-05T13:22:56.659397+00:00; test=hermes_smoke

- Smoke test from Codex: verify deterministic ingestion pipeline writes via scripts/ingest.py, not direct Markdown file creation.

### 2026-05-06 — codex-smoke/text

Source: source_type=text; source_app=codex-smoke; captured_at=2026-05-06T22:36:00+10:00; kind=smoke_test

- Post-reboot smoke test for Hermes Agent
- Gateway, oMLX, API, web search, and ingestion pipeline were checked.

## References

### 2026-05-03T23:14:59+10:00 - manual/router

- Router model: Qwen2.5-7B-Instruct-4bit
- Selected route: tool_first_obsidian
- Selected model: Qwen2.5-7B-Instruct-4bit
- Tool action: run_ingest
- Reason: Qwen detected durable Obsidian capture intent; use the ingestion pipeline before freeform file writes.

### 2026-05-03T23:20:29+10:00 - webui/router

- Router model: Qwen2.5-7B-Instruct-4bit
- Selected route: tool_first_obsidian
- Selected model: Qwen2.5-7B-Instruct-4bit
- Tool action: run_ingest
- Reason: 用户需要将文本内容写入Obsidian的inbox，这需要使用Obsidian工具来完成。

### 2026-05-03T23:20:50+10:00 - manual/router

- Router model: Qwen2.5-7B-Instruct-4bit
- Selected route: tool_first_obsidian
- Selected model: Qwen2.5-7B-Instruct-4bit
- Tool action: run_ingest
- Reason: 用户要求将内容写入Obsidian inbox，符合tool_first_obsidian的使用条件

### 2026-05-04T08:00:27+10:00 - webui/router

- Router model: Qwen2.5-7B-Instruct-4bit
- Selected route: tool_first_obsidian
- Selected model: Qwen2.5-7B-Instruct-4bit
- Tool action: run_ingest
- Reason: Qwen detected durable Obsidian capture intent; use the ingestion pipeline before freeform file writes.

### 2026-05-05T21:28:27+10:00 - wechat/router

- Router model: Qwen2.5-7B-Instruct-4bit
- Selected route: tool_first_obsidian
- Selected model: Qwen2.5-7B-Instruct-4bit
- Tool action: run_ingest
- Reason: Qwen detected durable Obsidian capture intent; use the ingestion pipeline before freeform file writes.

### 2026-05-05T21:28:57+10:00 - local_web/router

- Router model: Qwen2.5-7B-Instruct-4bit
- Selected route: direct_qwen
- Selected model: Qwen2.5-7B-Instruct-4bit
- Tool action: none
- Reason: Qwen can answer directly without model escalation.

### 2026-05-05T21:28:57+10:00 - wechat/router

- Router model: Qwen2.5-7B-Instruct-4bit
- Selected route: tool_first_obsidian
- Selected model: Qwen2.5-7B-Instruct-4bit
- Tool action: run_ingest
- Reason: Qwen detected durable Obsidian capture intent; use the ingestion pipeline before freeform file writes.

### 2026-05-05T21:28:57+10:00 - telegram/router

- Router model: Qwen2.5-7B-Instruct-4bit
- Selected route: delegate_hermes_complex
- Selected model: Hermes-3-Llama-3.1-8B-4bit
- Tool action: none
- Reason: Qwen marked the request as complex enough to delegate to Hermes for deeper multi-step reasoning.

### 2026-05-05T23:19:30+10:00 - manual/router

- Router model: Qwen2.5-7B-Instruct-4bit
- Selected route: direct_qwen
- Selected model: Qwen2.5-7B-Instruct-4bit
- Tool action: none
- Reason: Qwen can answer directly without model escalation.

### 2026-05-05T23:19:30+10:00 - manual/router

- Router model: Qwen2.5-7B-Instruct-4bit
- Selected route: tool_first_obsidian
- Selected model: Qwen2.5-7B-Instruct-4bit
- Tool action: run_ingest
- Reason: Qwen detected durable Obsidian capture intent; use the ingestion pipeline before freeform file writes.

### 2026-05-06T22:35:59+10:00 - manual/router

- Router model: Qwen2.5-7B-Instruct-4bit
- Selected route: direct_qwen
- Selected model: Qwen2.5-7B-Instruct-4bit
- Tool action: none
- Reason: Qwen can answer directly without model escalation.

### 2026-05-10T20:34:02+10:00 - wechat/router

- Router model: Qwen2.5-7B-Instruct-4bit
- Selected route: tool_first_obsidian
- Selected model: Qwen2.5-7B-Instruct-4bit
- Tool action: run_ingest
- Reason: Qwen detected durable Obsidian capture intent; use the ingestion pipeline before freeform file writes.

### 2026-05-10T20:34:02+10:00 - telegram/router

- Router model: Qwen2.5-7B-Instruct-4bit
- Selected route: delegate_hermes_complex
- Selected model: Hermes-3-Llama-3.1-8B-4bit
- Tool action: none
- Reason: Qwen marked the request as complex enough to delegate to Hermes for deeper multi-step reasoning.

### 2026-05-10T20:34:02+10:00 - local_web/router

- Router model: Qwen2.5-7B-Instruct-4bit
- Selected route: direct_qwen
- Selected model: Qwen2.5-7B-Instruct-4bit
- Tool action: none
- Reason: Qwen can answer directly without model escalation.

### 2026-05-13T23:13:01+10:00 - wechat/router

- Router model: Qwen2.5-7B-Instruct-4bit
- Selected route: tool_first_obsidian
- Selected model: Qwen2.5-7B-Instruct-4bit
- Tool action: run_ingest
- Reason: Qwen detected durable Obsidian capture intent; use the ingestion pipeline before freeform file writes.

### 2026-05-13T23:13:01+10:00 - local_web/router

- Router model: Qwen2.5-7B-Instruct-4bit
- Selected route: direct_qwen
- Selected model: Qwen2.5-7B-Instruct-4bit
- Tool action: none
- Reason: Qwen can answer directly without model escalation.

### 2026-05-13T23:13:01+10:00 - telegram/router

- Router model: Qwen2.5-7B-Instruct-4bit
- Selected route: delegate_hermes_complex
- Selected model: Hermes-3-Llama-3.1-8B-4bit
- Tool action: none
- Reason: Qwen marked the request as complex enough to delegate to Hermes for deeper multi-step reasoning.

### 2026-05-15T15:51:16+10:00 - wechat/router

- Router model: Qwen2.5-7B-Instruct-4bit
- Selected route: tool_first_obsidian
- Selected model: Qwen2.5-7B-Instruct-4bit
- Tool action: run_ingest
- Reason: Qwen detected durable Obsidian capture intent; use the ingestion pipeline before freeform file writes.

### 2026-05-15T15:51:27+10:00 - wechat/router

- Router model: Qwen2.5-7B-Instruct-4bit
- Selected route: tool_first_obsidian
- Selected model: Qwen2.5-7B-Instruct-4bit
- Tool action: run_ingest
- Reason: Qwen detected durable Obsidian capture intent; use the ingestion pipeline before freeform file writes.

### 2026-05-15T22:30:21+10:00 - wechat/router

- Router model: Qwen2.5-7B-Instruct-4bit
- Selected route: direct_qwen
- Selected model: Qwen2.5-7B-Instruct-4bit
- Tool action: none
- Reason: Qwen can answer directly without model escalation.

### 2026-05-15T22:30:21+10:00 - wechat/router

- Router model: Qwen2.5-7B-Instruct-4bit
- Selected route: tool_first_obsidian
- Selected model: Qwen2.5-7B-Instruct-4bit
- Tool action: run_ingest
- Reason: Qwen detected high-value knowledge in chat content; promote through ingestion without requiring an explicit save command.

### 2026-05-15T22:30:55+10:00 - wechat/router

- Router model: Qwen2.5-7B-Instruct-4bit
- Selected route: tool_first_obsidian
- Selected model: Qwen2.5-7B-Instruct-4bit
- Tool action: run_ingest
- Reason: Qwen detected high-value knowledge in chat content; promote through ingestion without requiring an explicit save command.

### 2026-05-16T11:13:26+10:00 - wechat/router

- Router model: Qwen3.5-4B-OptiQ-4bit
- Selected route: tool_first_obsidian
- Selected model: Qwen3.5-4B-OptiQ-4bit
- Tool action: run_ingest
- Reason: Qwen detected durable Obsidian capture intent; use the ingestion pipeline before freeform file writes.

### 2026-05-16T14:51:36+10:00 - wechat/router

- Router model: Qwen3.5-4B-OptiQ-4bit
- Selected route: tool_first_obsidian
- Selected model: Qwen3.5-4B-OptiQ-4bit
- Tool action: run_ingest
- Reason: Qwen detected high-value knowledge in chat content; promote through ingestion without requiring an explicit save command.

### 2026-05-16T16:08:41+10:00 - wechat/router

- Router model: Qwen3.5-4B-OptiQ-4bit
- Selected route: tool_first_obsidian
- Selected model: Qwen3.5-4B-OptiQ-4bit
- Tool action: run_ingest
- Reason: Qwen detected durable Obsidian capture intent; use the ingestion pipeline before freeform file writes.

### 2026-05-16T19:19:33+10:00 - wechat/router

- Router model: Qwen3.5-4B-OptiQ-4bit
- Selected route: tool_first_obsidian
- Selected model: Qwen3.5-4B-OptiQ-4bit
- Tool action: run_ingest
- Reason: Qwen detected durable Obsidian capture intent; use the ingestion pipeline before freeform file writes.
