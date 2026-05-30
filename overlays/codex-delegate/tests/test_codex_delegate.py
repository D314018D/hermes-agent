import os
import unittest

from tools.codex_delegate import ContextPack, build_child_env, delegate


def context(**overrides):
    data = {
        "task_id": "test-1",
        "task_hash": "sha256:test",
        "user_goal": "Debug this Python repository test failure.",
        "privacy_level": "public",
        "route_reason": "complex coding task",
        "allowed_working_directory": str(__import__("pathlib").Path(__file__).resolve().parents[1]),
        "api_fallback_allowed": False,
        "api_fallback_approved": False,
        "dry_run": True,
    }
    data.update(overrides)
    return ContextPack.from_mapping(data)


class CodexDelegateTests(unittest.TestCase):
    def test_public_complex_task_dry_run_ok(self):
        result = delegate(context())
        self.assertEqual(result["status"], "ok")
        self.assertIn("task_summary", result)
        self.assertIn("memory_candidate", result)
        self.assertIn("skill_candidate", result)

    def test_ordinary_rewrite_rejected_as_out_of_scope(self):
        result = delegate(
            context(
                user_goal="Rewrite this sentence to sound nicer.",
                route_reason="ordinary rewrite",
            )
        )
        self.assertEqual(result["status"], "failed")
        self.assertIn("outside Codex delegate scope", result["error"])

    def test_private_task_blocks_cloud_fallback(self):
        result = delegate(
            context(
                privacy_level="private",
                codex_profile="chatgpt_codex",
                user_goal="Debug this private customer project repository.",
            )
        )
        self.assertEqual(result["status"], "blocked_private_cloud")

    def test_secret_input_blocked(self):
        result = delegate(
            context(
                privacy_level="public",
                user_goal="Debug this script that contains an API key.",
            )
        )
        self.assertEqual(result["status"], "blocked_secret")

    def test_public_quota_exhausted_needs_api_approval(self):
        result = delegate(
            context(
                dry_run=False,
                simulate_codex_output="usage limit reached",
                api_fallback_allowed=True,
            )
        )
        self.assertEqual(result["status"], "need_api_approval")

    def test_private_quota_exhausted_no_fallback(self):
        result = delegate(
            context(
                privacy_level="private",
                codex_profile="local_private",
                dry_run=False,
                simulate_codex_output="rate limit",
            )
        )
        self.assertEqual(result["status"], "quota_exhausted_private_no_fallback")

    def test_api_key_stripped_unless_approved(self):
        old = os.environ.get("OPENAI_API_KEY")
        os.environ["OPENAI_API_KEY"] = "should-not-leak"
        try:
            env = build_child_env(api_fallback_approved=False)
            self.assertNotIn("OPENAI_API_KEY", env)
            approved_env = build_child_env(api_fallback_approved=True)
            self.assertEqual(approved_env.get("OPENAI_API_KEY"), "should-not-leak")
        finally:
            if old is None:
                os.environ.pop("OPENAI_API_KEY", None)
            else:
                os.environ["OPENAI_API_KEY"] = old


if __name__ == "__main__":
    unittest.main()
