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


if __name__ == "__main__":
    unittest.main()
