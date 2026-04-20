import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
APPROVAL_GATE = REPO_ROOT / "scripts" / "approval-gate.py"


class ApprovalGateTests(unittest.TestCase):
    def _write_transcript(self, user_text: str) -> Path:
        handle = tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8")
        with handle as f:
            f.write(
                json.dumps(
                    {
                        "type": "user",
                        "message": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": user_text,
                                }
                            ]
                        },
                    }
                )
                + "\n"
            )
        return Path(handle.name)

    def _run_gate(self, payload: dict, transcript_text: str | None = None) -> subprocess.CompletedProcess[str]:
        transcript_path = None
        if transcript_text is not None:
            transcript_path = self._write_transcript(transcript_text)
            payload = {**payload, "transcript_path": str(transcript_path)}
        result = subprocess.run(
            [sys.executable, str(APPROVAL_GATE)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=False,
        )
        if transcript_path is not None:
            transcript_path.unlink(missing_ok=True)
        return result

    def test_wrapper_emits_structured_deny_decision(self) -> None:
        result = self._run_gate(
            {
                "tool_name": "mcp__ha-mcp__ha_config_entries_flow",
                "tool_input": {"handler": "hue"},
            },
            transcript_text="please continue",
        )

        self.assertEqual(result.returncode, 0)
        decision = json.loads(result.stdout)
        self.assertEqual(decision["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn("Reply yes to confirm or no to cancel.", decision["hookSpecificOutput"]["permissionDecisionReason"])

    def test_wrapper_allows_confirmed_call_silently(self) -> None:
        result = self._run_gate(
            {
                "tool_name": "mcp__ha-mcp__ha_config_entries_flow",
                "tool_input": {"handler": "hue"},
            },
            transcript_text="yes",
        )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_wrapper_allows_follow_up_step_silently(self) -> None:
        result = self._run_gate(
            {
                "tool_name": "mcp__ha-mcp__ha_config_entries_flow",
                "tool_input": {"handler": "hue", "flow_id": "abc123"},
            },
            transcript_text="please continue",
        )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_wrapper_allows_non_gated_tool_silently(self) -> None:
        result = self._run_gate(
            {
                "tool_name": "mcp__ha-mcp__ha_config_entries_get",
                "tool_input": {},
            },
            transcript_text="please continue",
        )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_wrapper_denies_device_mutation_without_confirmation(self) -> None:
        result = self._run_gate(
            {
                "tool_name": "mcp__ha-mcp__ha_update_device",
                "tool_input": {"device_id": "device-123"},
            },
            transcript_text="please continue",
        )

        self.assertEqual(result.returncode, 0)
        decision = json.loads(result.stdout)
        self.assertEqual(decision["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn("ha_update_device", decision["hookSpecificOutput"]["permissionDecisionReason"])

    def test_malformed_input_fails_open(self) -> None:
        result = subprocess.run(
            [sys.executable, str(APPROVAL_GATE)],
            input="{not json",
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
