"""Activation helpers for local/cloud route decisions.

This module keeps local/cloud execution policy out of gateway internals.  The
gateway owns message flow; this module owns whether a classified turn should
actually switch provider for the current turn.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from routing.local_cloud.classifier import RouteDecision


@dataclass(frozen=True)
class ActiveRouteRuntime:
    model: str
    runtime: dict[str, Any]
    reason: str


def should_activate_route(
    decision: RouteDecision | None,
    config: Mapping[str, Any] | None = None,
) -> bool:
    if decision is None or not decision.enabled:
        return False
    if decision.route not in {"cloud", "hybrid"}:
        return False

    split_cfg = _split_config(config)
    mode = str(decision.mode or split_cfg.get("mode") or "").strip().lower()
    activation_cfg = _as_mapping(split_cfg.get("activation"))

    if mode == "active":
        active_task_types = _as_str_set(activation_cfg.get("active_task_types"))
        return not active_task_types or decision.task_type in active_task_types

    if mode == "selective":
        selected = _as_str_set(activation_cfg.get("active_task_types"))
        selected |= _as_str_set(activation_cfg.get("selective_task_types"))
        return bool(selected) and decision.task_type in selected

    return False


def resolve_active_route_runtime(
    decision: RouteDecision,
    config: Mapping[str, Any] | None = None,
) -> ActiveRouteRuntime | None:
    if not should_activate_route(decision, config):
        return None

    from hermes_cli.models import get_default_model_for_provider
    from hermes_cli.model_normalize import normalize_model_for_provider
    from hermes_cli.runtime_provider import resolve_runtime_provider

    split_cfg = _split_config(config)
    provider = decision.cloud_provider or str(split_cfg.get("cloud_provider") or "")
    if not provider:
        return None

    runtime = resolve_runtime_provider(requested=provider)
    resolved_provider = str(runtime.get("provider") or provider)
    model = decision.cloud_model or str(split_cfg.get("cloud_model") or "")
    if not model:
        model = str(runtime.get("model") or "")
    if not model:
        model = get_default_model_for_provider(resolved_provider) or ""
    if model:
        model = normalize_model_for_provider(model, resolved_provider)

    config_context_length = _resolve_context_length(split_cfg, config)

    active_runtime = {
        "api_key": runtime.get("api_key"),
        "base_url": runtime.get("base_url"),
        "provider": runtime.get("provider"),
        "api_mode": runtime.get("api_mode"),
        "command": runtime.get("command"),
        "args": list(runtime.get("args") or []),
        "credential_pool": runtime.get("credential_pool"),
        "config_context_length": config_context_length,
    }
    return ActiveRouteRuntime(
        model=model,
        runtime=active_runtime,
        reason=f"{decision.route}:{decision.task_type}:{decision.matched_rule}",
    )


def _split_config(config: Mapping[str, Any] | None) -> Mapping[str, Any]:
    if not isinstance(config, Mapping):
        return {}
    agent = config.get("agent")
    if isinstance(agent, Mapping):
        split = agent.get("local_cloud_split")
        if isinstance(split, Mapping):
            return split
    return {}


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _as_str_set(value: Any) -> set[str]:
    if not value:
        return set()
    if isinstance(value, str):
        return {value.strip()} if value.strip() else set()
    if isinstance(value, (list, tuple, set)):
        return {str(item).strip() for item in value if str(item).strip()}
    return set()


def _resolve_context_length(split_cfg: Mapping[str, Any], config: Mapping[str, Any] | None) -> int:
    raw = split_cfg.get("cloud_context_length")
    if isinstance(raw, int) and raw > 0:
        return raw

    if isinstance(config, Mapping):
        complex_cfg = config.get("complex_model")
        if isinstance(complex_cfg, Mapping):
            raw = complex_cfg.get("context_length")
            if isinstance(raw, int) and raw > 0:
                return raw

    return 65536
