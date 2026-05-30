from agent.runtime import HermesAgentRuntime, ToolExecution
from core.schemas import HermesMessage


def test_wechat_text_gbrain_request_runs_ingest(monkeypatch, tmp_path):
    monkeypatch.setattr("agent.runtime.RUN_LOG_PATH", tmp_path / "dispatch.jsonl")
    monkeypatch.setattr("agent.runtime.HermesAgentRuntime._llm_plan", lambda self, message, model, fallback: fallback)
    monkeypatch.setattr(
        "agent.runtime.HermesAgentRuntime._run_gbrain_ingest",
        lambda self, payload, message: ToolExecution(tool="run_gbrain_ingest", ok=True, payload=payload, result={"should_store": True}),
    )

    result = HermesAgentRuntime().dispatch_payload(
        {
            "source": "wechat",
            "source_type": "wechat_text",
            "text": "请把这条内容写入 Obsidian inbox",
            "chat_id": "wx-1",
            "timestamp": "2026-05-05T09:00:00+10:00",
        }
    )

    assert result.route == "tool_first_gbrain_ingest"
    assert result.actions[0].tool == "run_gbrain_ingest"
    assert result.actions[0].ok is True
    assert result.reply == "已收到，我会交给 GBrain 的写入流程处理。"


def test_legacy_run_ingest_action_maps_to_gbrain_ingest(monkeypatch):
    monkeypatch.setattr(
        "agent.runtime.HermesAgentRuntime._run_gbrain_ingest",
        lambda self, payload, message: ToolExecution(tool="run_gbrain_ingest", ok=True, payload=payload, result={"should_store": True}),
    )
    message = HermesMessage(
        message_id="msg-legacy",
        source="test",
        source_type="text",
        input_type="text",
        user_id="user",
        timestamp="2026-05-29T00:00:00+10:00",
        text="save this",
        language="en",
    )

    result = HermesAgentRuntime()._run_tool(message, {"tool": "run_ingest", "payload": {"content": "save this"}})

    assert result.tool == "run_gbrain_ingest"
    assert result.ok is True


def test_telegram_complex_request_enqueues_task(monkeypatch, tmp_path):
    monkeypatch.setattr("agent.runtime.QUEUE_PATH", tmp_path / "queue.jsonl")
    monkeypatch.setattr("agent.runtime.RUN_LOG_PATH", tmp_path / "dispatch.jsonl")
    monkeypatch.setattr("agent.runtime.HermesAgentRuntime._llm_plan", lambda self, message, model, fallback: fallback)

    result = HermesAgentRuntime().dispatch_payload(
        {
            "source": "telegram",
            "text": "please analyze this architecture and implement the refactor",
            "user_id": "tg-user",
            "chat_id": "tg-chat",
            "message_id": "msg-1",
            "timestamp": "2026-05-05T09:05:00+10:00",
        }
    )

    assert result.route == "delegate_hermes_complex"
    assert result.actions[0].tool == "enqueue_task"
    assert result.actions[0].ok is True


def test_local_web_direct_reply(monkeypatch, tmp_path):
    monkeypatch.setattr("agent.runtime.RUN_LOG_PATH", tmp_path / "dispatch.jsonl")
    monkeypatch.setattr("agent.runtime.HermesAgentRuntime._llm_plan", lambda self, message, model, fallback: fallback)

    result = HermesAgentRuntime().dispatch_payload(
        {
            "source": "local_web",
            "content": "router status",
            "session_id": "web-1",
            "timestamp": "2026-05-05T09:10:00+10:00",
        }
    )

    assert result.route == "direct_qwen"
    assert result.actions[0].tool == "reply_only"
    assert result.reply == "router status"
