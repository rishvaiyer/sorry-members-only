import subprocess
import unittest

from members_only.adapters import ObscuraActionAdapter
from members_only.models import Proposal


class ObscuraAdapterTests(unittest.TestCase):
    def test_fetch_uses_obscura_and_returns_bounded_summary(self):
        calls = []

        def runner(command):
            calls.append(tuple(command))
            return subprocess.CompletedProcess(command, 0, "private page body", "")

        proposal = Proposal(
            member_id="member-1",
            agent_id="agent-1",
            action="browser_fetch",
            destination="external:web",
            payload={"url": "https://example.com"},
        )

        result = ObscuraActionAdapter(runner=runner).execute(proposal)

        self.assertTrue(result.success)
        self.assertIn("bytes", result.summary)
        self.assertNotIn("private page body", result.summary)
        self.assertEqual(
            calls[0],
            ("obscura", "fetch", "https://example.com", "--dump", "text", "--quiet"),
        )

    def test_rejects_non_http_urls(self):
        proposal = Proposal(
            member_id="member-1",
            agent_id="agent-1",
            action="browser_fetch",
            destination="local:file",
            payload={"url": "file:///etc/passwd"},
        )

        with self.assertRaises(ValueError):
            ObscuraActionAdapter(runner=lambda _: None).execute(proposal)
