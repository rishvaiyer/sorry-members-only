import unittest
from unittest.mock import patch

from members_only import (
    DockerSandbox,
    SandboxCommandAdapter,
    SandboxResult,
    SandboxRuntimeDenied,
)
from members_only.models import Proposal


def make_proposal() -> Proposal:
    return Proposal(
        member_id="member-1",
        agent_id="agent-1",
        action="send_message",
        destination="local:test-inbox",
        payload={"body": "private worker input"},
    )


class FakeRuntime:
    def __init__(self, result: SandboxResult) -> None:
        self.result = result
        self.commands: list[tuple[str, ...]] = []

    def run(self, command, *, timeout_seconds=10.0):
        self.commands.append(tuple(command))
        return self.result


class DockerSandboxTests(unittest.TestCase):
    @patch("members_only.runtime.subprocess.run")
    def test_docker_command_has_hardening_flags(self, run):
        run.return_value.returncode = 0

        result = DockerSandbox(image="worker:local").run(("python", "-c", "pass"))

        argv = run.call_args.args[0]
        self.assertTrue(result.completed)
        self.assertIn("--network=none", argv)
        self.assertIn("--read-only", argv)
        self.assertIn("--cap-drop=ALL", argv)
        self.assertIn("--security-opt=no-new-privileges=true", argv)
        self.assertIn("--pull=never", argv)
        self.assertNotIn("--privileged", argv)
        self.assertEqual(argv[-3:], ["python", "-c", "pass"])

    @patch("members_only.runtime.subprocess.run", side_effect=FileNotFoundError)
    def test_missing_runtime_fails_closed(self, _run):
        result = DockerSandbox(image="worker:local").run(("true",))

        self.assertFalse(result.completed)
        self.assertEqual(result.reason, "runtime_unavailable")


class SandboxCommandAdapterTests(unittest.TestCase):
    def test_completed_worker_returns_safe_action_result(self):
        runtime = FakeRuntime(SandboxResult(True, 0, "completed"))
        adapter = SandboxCommandAdapter(runtime=runtime, command=("worker", "run"))

        result = adapter.execute(make_proposal())

        self.assertTrue(result.success)
        self.assertEqual(runtime.commands, [("worker", "run")])

    def test_denied_worker_never_becomes_a_success(self):
        runtime = FakeRuntime(SandboxResult(False, None, "runtime_unavailable"))
        adapter = SandboxCommandAdapter(runtime=runtime, command=("worker", "run"))

        with self.assertRaises(SandboxRuntimeDenied) as raised:
            adapter.execute(make_proposal())

        self.assertEqual(raised.exception.result.reason, "runtime_unavailable")


if __name__ == "__main__":
    unittest.main()
