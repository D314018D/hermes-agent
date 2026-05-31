"""Chinese-first routing heuristics for local/cloud split.

These rules are deterministic and platform-aware. They intentionally avoid
touching Hermes execution flow; they only influence shadow classification.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


FORCE_CLOUD_TERMS = (
    "codex",
    "走云",
    "云端",
)

FORCE_LOCAL_TERMS = (
    "不要去上网",
    "不要上网",
    "别上网",
    "本地模型",
    "本地的最强模型",
    "直接用本地",
    "仅用本地",
    "只用本地",
    "本地分析",
)

TASK_RULES: tuple[tuple[str, tuple[str, ...], str], ...] = (
    ("debugging", ("排查", "调试", "定位", "复现", "出了什么问题", "哪里有问题", "检查一下", "检查", "bug", "报错", "日志"), "zh_debugging_term"),
    ("planning", ("规划", "计划", "方案", "路线图", "roadmap", "梳理", "落地", "执行计划", "修复方案"), "zh_planning_term"),
    ("architecture", ("架构", "设计方案", "系统设计", "取舍", "tradeoff"), "zh_architecture_term"),
    ("coding", ("修复", "改代码", "写代码", "补丁", "实现", "修一下"), "zh_coding_term"),
    ("memory", ("记录：", "记一下", "记住", "存一下", "存档"), "zh_memory_term"),
    ("ingestion", ("整理成笔记", "归档", "入库", "导入"), "zh_ingestion_term"),
    ("reminders", ("定时任务", "提醒", "重新发", "天气预报", "今天的"), "zh_reminders_term"),
    ("obsidian", ("obsidian", "知识库", "笔记"), "zh_obsidian_term"),
)


@dataclass(frozen=True)
class ZhRuleMatch:
    route: str
    task_type: str
    matched_rule: str
    confidence: float
    reason: str


def detect_zh_rule(
    text: str,
    *,
    platform: str = "",
    config: Mapping[str, Any] | None = None,
) -> ZhRuleMatch | None:
    lower = (text or "").lower()
    platform_cfg = _platform_policy(config, platform)

    force_local_terms = tuple(platform_cfg.get("force_local_terms") or FORCE_LOCAL_TERMS)
    for term in force_local_terms:
        if term and term.lower() in lower:
            return ZhRuleMatch(
                route="local",
                task_type=_forced_local_task_type(lower),
                matched_rule=f"force_local_terms:{term}",
                confidence=0.98,
                reason="zh_force_local_term",
            )

    force_cloud_terms = tuple(platform_cfg.get("force_cloud_terms") or FORCE_CLOUD_TERMS)
    for term in force_cloud_terms:
        if term and term.lower() in lower:
            return ZhRuleMatch(
                route="cloud",
                task_type=_forced_cloud_task_type(lower),
                matched_rule=f"force_cloud_terms:{term}",
                confidence=0.95,
                reason="zh_force_cloud_term",
            )

    for task_type, terms, rule_name in TASK_RULES:
        for term in terms:
            if term and term.lower() in lower:
                route = "cloud" if task_type in {"coding", "debugging", "architecture", "planning"} else "local"
                confidence = 0.9 if route == "cloud" else 0.86
                return ZhRuleMatch(
                    route=route,
                    task_type=task_type,
                    matched_rule=f"{rule_name}:{term}",
                    confidence=confidence,
                    reason=rule_name,
                )

    return None


def _forced_cloud_task_type(lower: str) -> str:
    if any(term in lower for term in ("排查", "调试", "问题", "检查")):
        return "debugging"
    if any(term in lower for term in ("规划", "计划", "方案", "路线图", "roadmap", "梳理", "落地", "执行计划")):
        return "planning"
    if any(term in lower for term in ("架构", "设计", "取舍", "tradeoff")):
        return "architecture"
    if any(term in lower for term in ("修复", "改代码", "写代码", "实现")):
        return "coding"
    return "coding"


def _forced_local_task_type(lower: str) -> str:
    if any(term in lower for term in ("排查", "调试", "问题", "检查", "报错", "日志")):
        return "debugging"
    if any(term in lower for term in ("规划", "计划", "方案", "路线图", "roadmap", "梳理", "落地", "执行计划")):
        return "planning"
    if any(term in lower for term in ("架构", "设计", "取舍", "tradeoff")):
        return "architecture"
    if any(term in lower for term in ("修复", "改代码", "写代码", "实现")):
        return "coding"
    return "quick_chat"


def _platform_policy(config: Mapping[str, Any] | None, platform: str) -> Mapping[str, Any]:
    if not isinstance(config, Mapping):
        return {}
    agent = config.get("agent")
    if not isinstance(agent, Mapping):
        return {}
    split = agent.get("local_cloud_split")
    if not isinstance(split, Mapping):
        return {}
    policies = split.get("platform_policies")
    if not isinstance(policies, Mapping):
        return {}
    selected = policies.get(platform or "")
    return selected if isinstance(selected, Mapping) else {}
