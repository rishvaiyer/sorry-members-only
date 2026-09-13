import io
import unittest
from contextlib import redirect_stdout

from members_only.cli import main


class CliDemoTests(unittest.TestCase):
    def test_demo_prints_trace_events_and_hides_private_payload(self):
        output = io.StringIO()

        with redirect_stdout(output):
            exit_code = main(["demo"])

        text = output.getvalue()
        self.assertEqual(exit_code, 0)
        self.assertIn("proposal_received", text)
        self.assertIn("sensitivity_checked", text)
        self.assertIn("approval_recorded", text)
        self.assertIn("action_executed", text)
        self.assertIn("execution_blocked", text)
        self.assertIn("Entering proposal intake check", text)
        self.assertIn("Sensitivity check completed", text)
        self.assertIn("Sandbox shield passed", text)
        self.assertIn("Entering replay test", text)
        self.assertIn('"status": "denied"', text)
        self.assertNotIn("member-private-content", text)

    def test_attack_demo_shows_fail_closed_scenarios(self):
        output = io.StringIO()

        with redirect_stdout(output):
            exit_code = main(["attack-demo"])

        text = output.getvalue()
        self.assertEqual(exit_code, 0)
        self.assertIn("Tampered proposal", text)
        self.assertIn("Invalid machine attestation", text)
        self.assertIn("Broker denial", text)
        self.assertIn("Expired capability", text)
        self.assertIn("One-use capability replay", text)
        self.assertIn("Attack demo summary: 5/5 scenarios blocked or contained.", text)
        self.assertNotIn("member-private-content", text)
        self.assertNotIn("tampered-after-approval", text)


if __name__ == "__main__":
    unittest.main()
