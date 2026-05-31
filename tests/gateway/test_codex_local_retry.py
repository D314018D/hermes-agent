from gateway.run import GatewayRunner


def test_should_retry_locally_after_codex_failure_matches_known_client_error():
    result = {
        "failed": True,
        "provider": "openai-codex",
        "error": "'NoneType' object is not iterable",
    }

    assert GatewayRunner._should_retry_locally_after_codex_failure(result) is True


def test_should_retry_locally_after_codex_failure_rejects_other_failures():
    wrong_provider = {
        "failed": True,
        "provider": "custom",
        "error": "'NoneType' object is not iterable",
    }
    wrong_error = {
        "failed": True,
        "provider": "openai-codex",
        "error": "request timed out",
    }

    assert GatewayRunner._should_retry_locally_after_codex_failure(wrong_provider) is False
    assert GatewayRunner._should_retry_locally_after_codex_failure(wrong_error) is False


def test_consume_local_cloud_route_bypass_is_one_shot():
    runner = object.__new__(GatewayRunner)
    runner._local_cloud_route_bypass_once = {"agent:main:weixin:dm:test"}

    assert runner._consume_local_cloud_route_bypass("agent:main:weixin:dm:test") is True
    assert runner._consume_local_cloud_route_bypass("agent:main:weixin:dm:test") is False
