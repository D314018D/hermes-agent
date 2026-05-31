import json
import sys
from pathlib import Path

from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) in sys.path:
    sys.path.remove(str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT))

from routing.local_cloud import (
    classify_message,
    resolve_active_route_runtime,
    should_activate_route,
    write_route_decision,
)


def _config(path="logs/local-cloud-routing.jsonl"):
    return {
        "agent": {
            "local_cloud_split": {
                "enabled": True,
                "mode": "shadow",
                "default_route": "local",
                "cloud_provider": "openai-codex",
                "cloud_model": "gpt-5.4",
                "cloud_context_length": 65536,
                "ask_when_confidence_below": 0.55,
                "local_if": {"max_context_tokens": 6000},
                "cloud_if": {"min_context_tokens": 6000},
                "logging": {"enabled": True, "path": path},
                "platform_policies": {
                    "weixin": {
                        "force_cloud_terms": ["codex", "走云", "云端"],
                    }
                },
            }
        }
    }


def test_quick_chat_routes_local():
    decision = classify_message("what time is it?", _config(), platform="telegram")

    assert decision.route == "local"
    assert decision.task_type == "quick_chat"
    assert decision.mode == "shadow"
    assert decision.enabled is True
    assert decision.matched_rule == "default_question"


def test_coding_routes_cloud():
    decision = classify_message("Please implement the fix in gateway/run.py", _config())

    assert decision.route == "cloud"
    assert decision.task_type == "coding"
    assert "task_type_is_cloud_preferred" in decision.reasons


def test_repo_review_and_code_modification_routes_cloud():
    decision = classify_message("Please review this repo and modify the code.", _config())

    assert decision.route == "cloud"
    assert decision.task_type == "repo_refactor"
    assert decision.matched_rule == "matched_repo_refactor_keyword"
    assert "task_type_is_cloud_preferred" in decision.reasons


def test_cloud_task_with_local_state_routes_hybrid():
    decision = classify_message(
        "Plan a debugging pass for the Obsidian GBrain ingestion issue",
        _config(),
    )

    assert decision.route == "hybrid"
    assert decision.task_type == "debugging"
    assert "cloud_task_mentions_local_state" in decision.reasons


def test_large_context_routes_cloud():
    history = [{"role": "user", "content": "x" * 28000}]

    decision = classify_message("summarize this", _config(), history=history)

    assert decision.route == "cloud"
    assert decision.estimated_context_tokens >= 6000


def test_write_route_decision_jsonl(tmp_path):
    cfg = _config("logs/routes.jsonl")
    decision = classify_message("review this PR", cfg, session_id="s1")

    path = write_route_decision(decision, cfg, hermes_home=tmp_path)

    assert path == tmp_path / "logs" / "routes.jsonl"
    row = json.loads(path.read_text(encoding="utf-8"))
    assert row["route"] == "cloud"
    assert row["task_type"] == "pr_review"
    assert row["session_id"] == "s1"


def test_zh_force_cloud_term_uses_codex_route():
    decision = classify_message(
        "修复这个问题，通过走云的方式，用codex修复",
        _config(),
        platform="weixin",
    )

    assert decision.route == "cloud"
    assert decision.task_type == "debugging"
    assert decision.matched_rule == "force_cloud_terms:codex"


def test_zh_force_cloud_term_prefers_planning_over_coding():
    decision = classify_message(
        "用 codex 给我出一份 Hermes 本地/云端分流的规划方案",
        _config(),
        platform="weixin",
    )

    assert decision.route == "cloud"
    assert decision.task_type == "planning"
    assert decision.matched_rule == "force_cloud_terms:codex"


def test_zh_force_cloud_term_prefers_debugging_over_coding():
    decision = classify_message(
        "用 codex 帮我排查 Hermes 的报错日志，定位为什么微信发不出去",
        _config(),
        platform="weixin",
    )

    assert decision.route == "hybrid"
    assert decision.task_type == "debugging"
    assert decision.matched_rule == "force_cloud_terms:codex"


def test_zh_force_local_term_overrides_planning_cloud_route():
    decision = classify_message(
        "不要去上网，你直接用你本地的最强模型分析调Gbrain信息取查生成一个计划",
        _config(),
        platform="weixin",
    )

    assert decision.route == "local"
    assert decision.task_type == "planning"
    assert decision.matched_rule == "force_local_terms:不要去上网"


def test_zh_memory_record_term_routes_local_memory():
    decision = classify_message(
        "记录：正好跟骏总聊到未来T2 T23的客户管理事情",
        _config(),
        platform="weixin",
    )

    assert decision.route == "local"
    assert decision.task_type == "memory"
    assert decision.matched_rule == "zh_memory_term:记录："


def test_weixin_fixture_replay():
    fixture = Path("/Users/rl_home/.hermes/hermes-agent/tests/routing/fixtures/weixin_messages.jsonl")

    rows = [json.loads(line) for line in fixture.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert rows
    for row in rows:
        decision = classify_message(row["message"], _config(), platform="weixin")
        assert decision.route == row["expected_route"], row["message"]
        assert decision.task_type == row["expected_task_type"], row["message"]
        assert decision.matched_rule == row["expected_rule"], row["message"]


def test_shadow_route_does_not_activate():
    decision = classify_message("review this PR", _config())

    assert decision.route == "cloud"
    assert should_activate_route(decision, _config()) is False


def test_active_route_activates_cloud_tasks():
    cfg = _config()
    cfg["agent"]["local_cloud_split"]["mode"] = "active"
    decision = classify_message("review this PR", cfg)

    assert should_activate_route(decision, cfg) is True


def test_selective_route_activates_only_selected_task_types():
    cfg = _config()
    cfg["agent"]["local_cloud_split"]["mode"] = "selective"
    cfg["agent"]["local_cloud_split"]["activation"] = {
        "selective_task_types": ["debugging"],
    }

    review = classify_message("review this PR", cfg)
    debugging = classify_message("debug this traceback", cfg)

    assert should_activate_route(review, cfg) is False
    assert should_activate_route(debugging, cfg) is True


@patch("hermes_cli.runtime_provider.resolve_runtime_provider")
def test_active_route_resolves_codex_runtime(resolve_runtime_provider_mock):
    cfg = _config()
    cfg["agent"]["local_cloud_split"]["mode"] = "active"
    resolve_runtime_provider_mock.return_value = {
        "api_key": "oauth-token",
        "base_url": "https://chatgpt.com/backend-api/codex",
        "provider": "openai-codex",
        "api_mode": "codex_responses",
        "command": None,
        "args": [],
        "credential_pool": None,
    }
    decision = classify_message("修复这个问题，通过走云的方式，用codex修复", cfg, platform="weixin")

    active = resolve_active_route_runtime(decision, cfg)

    assert active is not None
    assert active.model == "gpt-5.4"
    assert active.runtime["provider"] == "openai-codex"
    assert active.runtime["api_mode"] == "codex_responses"
    assert active.runtime["config_context_length"] == 65536
    resolve_runtime_provider_mock.assert_called_once_with(requested="openai-codex")


@patch("hermes_cli.runtime_provider.resolve_runtime_provider")
def test_active_route_prefers_explicit_cloud_context_length(resolve_runtime_provider_mock):
    cfg = _config()
    cfg["agent"]["local_cloud_split"]["mode"] = "active"
    cfg["agent"]["local_cloud_split"]["cloud_context_length"] = 131072
    resolve_runtime_provider_mock.return_value = {
        "api_key": "oauth-token",
        "base_url": "https://chatgpt.com/backend-api/codex",
        "provider": "openai-codex",
        "api_mode": "codex_responses",
        "command": None,
        "args": [],
        "credential_pool": None,
    }
    decision = classify_message("修复这个问题，通过走云的方式，用codex修复", cfg, platform="weixin")

    active = resolve_active_route_runtime(decision, cfg)

    assert active is not None
    assert active.runtime["config_context_length"] == 131072
    resolve_runtime_provider_mock.assert_called_once_with(requested="openai-codex")


def test_selective_route_activates_planning_and_debugging():
    cfg = _config()
    cfg["agent"]["local_cloud_split"]["mode"] = "selective"
    cfg["agent"]["local_cloud_split"]["activation"] = {
        "selective_task_types": ["planning", "debugging"],
    }

    planning = classify_message(
        "用 codex 给我出一份 Hermes 本地/云端分流的规划方案",
        cfg,
        platform="weixin",
    )
    debugging = classify_message(
        "用 codex 帮我排查 Hermes 的报错日志，定位为什么微信发不出去",
        cfg,
        platform="weixin",
    )

    assert should_activate_route(planning, cfg) is True
    assert should_activate_route(debugging, cfg) is True
