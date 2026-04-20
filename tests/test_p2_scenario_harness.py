import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "p2_scenario_harness"
APPROVAL_GATE = REPO_ROOT / "scripts" / "approval-gate.py"


def load_scenarios() -> list[dict]:
    scenarios = []
    for path in sorted(FIXTURE_DIR.glob("*.json")):
        with path.open(encoding="utf-8") as handle:
            scenarios.append(json.load(handle))
    return scenarios


def load_scenario(name: str) -> dict:
    path = FIXTURE_DIR / f"{name}.json"
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def run_gate(tool_name: str, tool_input: dict, transcript: str) -> subprocess.CompletedProcess[str]:
    handle = tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8")
    with handle as transcript_file:
        transcript_file.write(
            json.dumps(
                {
                    "type": "user",
                    "message": {
                        "content": [
                            {
                                "type": "text",
                                "text": transcript,
                            }
                        ]
                    },
                }
            )
            + "\n"
        )
    transcript_path = Path(handle.name)
    try:
        return subprocess.run(
            [sys.executable, str(APPROVAL_GATE)],
            input=json.dumps(
                {
                    "tool_name": tool_name,
                    "tool_input": tool_input,
                    "transcript_path": str(transcript_path),
                }
            ),
            text=True,
            capture_output=True,
            check=False,
        )
    finally:
        transcript_path.unlink(missing_ok=True)


class P2ScenarioHarnessTests(unittest.TestCase):
    def test_discovers_named_fixtures(self) -> None:
        names = sorted(path.name for path in FIXTURE_DIR.glob("*.json"))

        self.assertIn("automation-step4.json", names)
        self.assertIn("discovery-routing.json", names)
        self.assertIn("confirmation-boundary.json", names)

    def test_loads_scenario_definitions(self) -> None:
        scenarios = load_scenarios()

        self.assertEqual(
            sorted(scenario["name"] for scenario in scenarios),
            ["automation-step4", "confirmation-boundary", "discovery-routing"],
        )
        for scenario in scenarios:
            self.assertIsInstance(scenario["docs"], list)
            self.assertIsInstance(scenario["tool_runs"], list)
            self.assertIsInstance(scenario["expect"], dict)
            self.assertGreater(len(scenario["docs"]), 0)
            self.assertGreater(len(scenario["tool_runs"]), 0)
            self.assertIn("name", scenario)
            self.assertIn("docs", scenario)
            self.assertIn("tool_runs", scenario)
            self.assertIn("expect", scenario)

    def test_fixture_schema_is_documented(self) -> None:
        readme = (FIXTURE_DIR / "README.md").read_text(encoding="utf-8")

        self.assertIn("name", readme)
        self.assertIn("docs", readme)
        self.assertIn("tool_runs", readme)
        self.assertIn("expect", readme)
        self.assertIn("confirmed", readme)
        self.assertIn("denied", readme)

    def test_discovery_then_confirmation_then_mutation(self) -> None:
        scenario = load_scenario("discovery-routing")
        discovery_doc = (REPO_ROOT / scenario["docs"][0]).read_text(encoding="utf-8")
        guide_doc = (REPO_ROOT / scenario["docs"][1]).read_text(encoding="utf-8")

        self.assertIn("ha_config_entries_get", discovery_doc)
        self.assertLess(discovery_doc.index("avahi-browse -atr"), discovery_doc.index("arp-scan --localnet"))
        self.assertLess(discovery_doc.index("arp-scan --localnet"), discovery_doc.index("nmap -sn"))
        self.assertIn("Discovery First", guide_doc)
        self.assertEqual(scenario["expect"]["read_only_discovery"], "allow")
        self.assertEqual(scenario["expect"]["denied_mutation"], "deny")
        self.assertEqual(scenario["expect"]["confirmed_follow_up"], "allow")

        self.assertEqual(len(scenario["tool_runs"]), 3)

        discovery_run, denied_run, confirmed_run = scenario["tool_runs"]

        discovery_result = run_gate(
            discovery_run["tool_name"],
            discovery_run["tool_input"],
            discovery_run["transcript"],
        )
        self.assertEqual(discovery_result.returncode, 0)
        self.assertEqual(discovery_result.stdout, "")

        denied_result = run_gate(
            denied_run["tool_name"],
            denied_run["tool_input"],
            denied_run["transcript"],
        )
        self.assertEqual(denied_result.returncode, 0)
        denied_decision = json.loads(denied_result.stdout)
        self.assertEqual(denied_decision["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn("explicit user confirmation", denied_decision["hookSpecificOutput"]["permissionDecisionReason"])

        confirmed_result = run_gate(
            confirmed_run["tool_name"],
            confirmed_run["tool_input"],
            confirmed_run["transcript"],
        )
        self.assertEqual(confirmed_result.returncode, 0)
        self.assertEqual(confirmed_result.stdout, "")

    def test_automation_step4_loads_pack_only_when_drafting(self) -> None:
        scenario = load_scenario("automation-step4")
        guide_doc = (REPO_ROOT / scenario["docs"][0]).read_text(encoding="utf-8")
        tools_router = (REPO_ROOT / scenario["docs"][1]).read_text(encoding="utf-8")
        best_practices = (REPO_ROOT / scenario["docs"][2]).read_text(encoding="utf-8")

        self.assertEqual(scenario["name"], "automation-step4")
        self.assertEqual(len(scenario["tool_runs"]), 2)
        self.assertIn("general automation request", scenario["tool_runs"][0]["transcript"].lower())
        self.assertIn("draft", scenario["tool_runs"][1]["transcript"].lower())
        self.assertIn("Step 4", guide_doc)
        self.assertIn("tools/ha-best-practices/", guide_doc)
        self.assertIn("advisory", guide_doc.lower())
        self.assertIn("CLAUDE.md", tools_router)
        self.assertIn("advisory", best_practices.lower())
        self.assertIn("CLAUDE.md", best_practices)


if __name__ == "__main__":
    unittest.main()
