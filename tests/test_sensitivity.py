import unittest

from members_only import inspect_proposal
from members_only.models import Proposal, SensitivityLevel


class SensitivityInspectorTests(unittest.TestCase):
    def test_detects_password_field_without_copying_secret_into_finding(self):
        secret = "correct-horse-battery-staple"
        proposal = Proposal(
            member_id="member-1",
            agent_id="agent-1",
            action="save_note",
            destination="local:test-inbox",
            payload={"password": secret},
        )

        findings = inspect_proposal(proposal)

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].category, "credential")
        self.assertEqual(findings[0].level, SensitivityLevel.CRITICAL)
        self.assertEqual(findings[0].field, "password")
        self.assertNotIn(secret, repr(findings[0]))

    def test_detects_nested_api_key_field_using_its_path(self):
        secret = "sk-live-example"
        proposal = Proposal(
            member_id="member-1",
            agent_id="agent-1",
            action="save_settings",
            destination="local:test-inbox",
            payload={"integration": {"api_key": secret}},
        )

        findings = inspect_proposal(proposal)

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].category, "credential")
        self.assertEqual(findings[0].field, "integration.api_key")
        self.assertNotIn(secret, repr(findings[0]))

    def test_detects_secret_like_text_even_when_field_name_is_generic(self):
        secret = "sk-live-1234567890abcdef"
        proposal = Proposal(
            member_id="member-1",
            agent_id="agent-1",
            action="save_note",
            destination="local:test-inbox",
            payload={"notes": f"temporary credential: {secret}"},
        )

        findings = inspect_proposal(proposal)

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].category, "credential")
        self.assertEqual(findings[0].field, "notes")
        self.assertNotIn(secret, repr(findings[0]))

    def test_marks_outbound_message_body_as_private_content(self):
        proposal = Proposal(
            member_id="member-1",
            agent_id="agent-1",
            action="send_message",
            destination="local:test-inbox",
            payload={"body": "Please keep this between us."},
        )

        findings = inspect_proposal(proposal)

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].category, "private_message")
        self.assertEqual(findings[0].level, SensitivityLevel.HIGH)
        self.assertEqual(findings[0].field, "body")

    def test_leaves_an_ordinary_local_note_unflagged(self):
        proposal = Proposal(
            member_id="member-1",
            agent_id="agent-1",
            action="save_note",
            destination="local:test-inbox",
            payload={"title": "status", "body": "The task is complete."},
        )

        self.assertEqual(inspect_proposal(proposal), ())

    def test_detects_personal_email_field(self):
        proposal = Proposal(
            member_id="member-1",
            agent_id="agent-1",
            action="save_profile",
            destination="local:test-inbox",
            payload={"email": "person@example.com"},
        )

        findings = inspect_proposal(proposal)

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].category, "personal_data")
        self.assertEqual(findings[0].level, SensitivityLevel.HIGH)
        self.assertEqual(findings[0].field, "email")


if __name__ == "__main__":
    unittest.main()
