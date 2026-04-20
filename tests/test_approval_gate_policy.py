import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from approval_gate_policy import evaluate_payload, extract_last_user_text, is_confirmation


class ApprovalGatePolicyTests(unittest.TestCase):
    def _write_transcript(self, entries: list[dict]) -> Path:
        handle = tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8")
        with handle as transcript_file:
            for entry in entries:
                transcript_file.write(json.dumps(entry) + "\n")
        return Path(handle.name)

    def test_denies_new_config_flow_without_confirmation(self) -> None:
        transcript_path = self._write_transcript(
            [
                {
                    "type": "user",
                    "message": {
                        "content": [
                            {
                                "type": "text",
                                "text": "please continue",
                            }
                        ]
                    },
                }
            ]
        )
        try:
            decision = evaluate_payload(
                {
                    "tool_name": "mcp__ha-mcp__ha_config_entries_flow",
                    "tool_input": {"handler": "hue"},
                    "transcript_path": str(transcript_path),
                }
            )
        finally:
            transcript_path.unlink(missing_ok=True)

        self.assertIsNotNone(decision)
        self.assertEqual(decision.decision, "deny")
        self.assertIn("explicit user confirmation", decision.reason)

    def test_allows_confirmed_new_config_flow(self) -> None:
        transcript_path = self._write_transcript(
            [
                {
                    "type": "user",
                    "message": {
                        "content": [
                            {
                                "type": "text",
                                "text": "yes",
                            }
                        ]
                    },
                }
            ]
        )
        try:
            decision = evaluate_payload(
                {
                    "tool_name": "mcp__ha-mcp__ha_config_entries_flow",
                    "tool_input": {"handler": "hue"},
                    "transcript_path": str(transcript_path),
                }
            )
        finally:
            transcript_path.unlink(missing_ok=True)

        self.assertIsNone(decision)

    def test_allows_follow_up_config_flow_step_without_fresh_confirmation(self) -> None:
        decision = evaluate_payload(
            {
                "tool_name": "mcp__ha-mcp__ha_config_entries_flow",
                "tool_input": {"handler": "hue", "flow_id": "abc123"},
                "transcript_path": "/tmp/does-not-matter",
            }
        )

        self.assertIsNone(decision)

    def test_allows_non_gated_tool(self) -> None:
        decision = evaluate_payload(
            {
                "tool_name": "mcp__ha-mcp__ha_config_entries_get",
                "tool_input": {},
                "transcript_path": "/tmp/does-not-matter",
            }
        )

        self.assertIsNone(decision)

    def test_denies_device_mutation_without_confirmation(self) -> None:
        transcript_path = self._write_transcript(
            [
                {
                    "type": "user",
                    "message": {
                        "content": [
                            {
                                "type": "text",
                                "text": "please continue",
                            }
                        ]
                    },
                }
            ]
        )
        try:
            decision = evaluate_payload(
                {
                    "tool_name": "mcp__ha-mcp__ha_update_device",
                    "tool_input": {"device_id": "device-123"},
                    "transcript_path": str(transcript_path),
                }
            )
        finally:
            transcript_path.unlink(missing_ok=True)

        self.assertIsNotNone(decision)
        self.assertEqual(decision.decision, "deny")
        self.assertIn("ha_update_device", decision.reason)

    def test_extract_last_user_text_ignores_tool_results(self) -> None:
        transcript_path = self._write_transcript(
            [
                {
                    "type": "user",
                    "message": {
                        "content": [
                            {
                                "type": "text",
                                "text": "yes",
                            }
                        ]
                    },
                },
                {
                    "type": "user",
                    "message": {
                        "content": [
                            {
                                "type": "tool_result",
                                "text": "not a real user reply",
                            }
                        ]
                    },
                },
            ]
        )
        try:
            text = extract_last_user_text(str(transcript_path))
        finally:
            transcript_path.unlink(missing_ok=True)

        self.assertIsNone(text)

    def test_confirmation_requires_short_affirmative_boundary(self) -> None:
        self.assertTrue(is_confirmation(" yes, go ahead"))
        self.assertTrue(is_confirmation("确认"))
        self.assertFalse(is_confirmation("please continue"))
        self.assertFalse(is_confirmation("yes " + ("really " * 20)))


if __name__ == "__main__":
    unittest.main()
