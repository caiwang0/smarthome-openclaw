# P2 Scenario Harness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic, no-HA P2 scenario harness that proves discovery routing, confirmation boundaries, ordered fallback, and automation Step 4 loading as one CI-friendly regression surface.

**Architecture:** Use one unittest entrypoint, `python3 -m unittest tests.test_p2_scenario_harness -v`, and drive every scenario from JSON fixtures under `tests/fixtures/p2_scenario_harness/`. The harness should shell out to the real `scripts/approval-gate.py`, read the live markdown docs under `tools/`, and assert combined behavior across discovery, approval, and automation paths without inventing a generic chat simulator or requiring a live Home Assistant instance. Keep the existing narrow tests in place as supporting unit coverage until the scenario harness proves equivalent or stronger coverage, then trim only duplicate assertions.

**Tech Stack:** Python 3 `unittest`, `json`, `subprocess`, `pathlib`, repo-local Markdown fixtures, shell commands.

---

## File Structure

- Create: `tests/test_p2_scenario_harness.py`
- Create: `tests/fixtures/p2_scenario_harness/README.md`
- Create: `tests/fixtures/p2_scenario_harness/discovery-routing.json`
- Create: `tests/fixtures/p2_scenario_harness/confirmation-boundary.json`
- Create: `tests/fixtures/p2_scenario_harness/automation-step4.json`
- Modify: `tests/test_approval_gate.py`
- Modify: `tests/test_automation_docs.py`
- Modify: `tests/test_integrations_docs.py`
- Create: `docs/p2-scenario-harness/validation-report.md`
- Modify: `docs/p2-scenario-harness/rdw-state.json`

---

## Phase 1: Harness core and reusable fixture schema

This phase addresses P1 and P3. It creates the dedicated harness entrypoint first, then locks the fixture schema so future scenarios do not require rewriting the runner.

### Task 1: Create the deterministic harness entrypoint and named scenario loader

**Files:**
- Create: `tests/test_p2_scenario_harness.py`
- Create: `tests/fixtures/p2_scenario_harness/discovery-routing.json`

- [ ] **Step 1: Write the failing harness test**

The first test should prove the module exists, discovers named fixtures, and can load a scenario definition with at least these fields: `name`, `docs`, `tool_runs`, and `expect`.

```python
def test_discovers_named_fixtures(self) -> None:
    names = sorted(path.name for path in FIXTURE_DIR.glob("*.json"))
    self.assertIn("discovery-routing.json", names)
    self.assertIn("confirmation-boundary.json", names)
```

- [ ] **Step 2: Run the harness test to verify it fails**

Run: `python3 -m unittest tests.test_p2_scenario_harness -v`
Expected: failure because `tests/test_p2_scenario_harness.py` and the fixture files do not exist yet.

- [ ] **Step 3: Implement the minimal runner**

Create a small loader that reads every `tests/fixtures/p2_scenario_harness/*.json` file, parses each scenario, and iterates through its steps in order. Keep the runner deterministic: no randomness, no network, no HA instance, no hidden defaults.

- [ ] **Step 4: Re-run the harness test**

Run: `python3 -m unittest tests.test_p2_scenario_harness -v`
Expected: pass once the module loads named fixtures and executes the scenario loop.

**Phase verification:** the repo now has a dedicated deterministic harness entrypoint and a reusable fixture loader. No scenario logic should live inline in the test body beyond the loader call and assertion dispatch.

### Task 2: Define the documented fixture schema and negative-path coverage

**Files:**
- Create: `tests/fixtures/p2_scenario_harness/README.md`
- Create: `tests/fixtures/p2_scenario_harness/confirmation-boundary.json`

- [ ] **Step 1: Write the failing schema test**

Add a test that reads the fixture README and confirms it documents the exact fields the harness consumes, plus at least one positive and one negative path.

```python
def test_fixture_schema_is_documented(self) -> None:
    readme = (FIXTURE_DIR / "README.md").read_text()
    self.assertIn("name", readme)
    self.assertIn("docs", readme)
    self.assertIn("tool_runs", readme)
    self.assertIn("expect", readme)
    self.assertIn("confirmed", readme)
    self.assertIn("denied", readme)
```

- [ ] **Step 2: Run the harness test to verify it fails**

Run: `python3 -m unittest tests.test_p2_scenario_harness -v`
Expected: failure because the schema README does not exist yet.

- [ ] **Step 3: Add the schema README and a negative fixture**

Document one JSON schema for all scenarios:

```json
{
  "name": "confirmation-boundary",
  "docs": ["tools/integrations/_guide.md"],
  "tool_runs": [
    {
      "tool_name": "mcp__ha-mcp__ha_config_entries_flow",
      "tool_input": {"handler": "hue"},
      "transcript": "please continue"
    }
  ],
  "expect": {
    "decision": "deny",
    "reason_contains": "explicit confirmation"
  }
}
```

Use that same shape for both positive and negative cases so the harness does not need special-case parsing.

- [ ] **Step 4: Re-run the harness test**

Run: `python3 -m unittest tests.test_p2_scenario_harness -v`
Expected: pass once the schema is documented and the negative-path fixture exists.

**Phase verification:** the harness now has a documented fixture contract that can express both allowed and denied flows without adding runner branches.

---

## Phase 2: Cross-scenario policy assertions

This phase addresses P2. It makes the harness prove the combined P2 journey instead of just checking isolated docs or hook behavior.

### Task 3: Exercise discovery-first routing, ordered fallback, and confirmation-gated mutation in one scenario

**Files:**
- Modify: `tests/test_p2_scenario_harness.py`
- Modify: `tests/test_approval_gate.py`
- Modify: `tests/fixtures/p2_scenario_harness/discovery-routing.json`

- [ ] **Step 1: Write the failing combined-flow test**

The combined scenario should assert all of the following in one path:

```python
def test_discovery_then_confirmation_then_mutation(self) -> None:
    self.assertIn("ha_config_entries_get", discovery_text)
    self.assertLess(discovery_text.index("avahi-browse -atr"), discovery_text.index("arp-scan --localnet"))
    self.assertLess(discovery_text.index("arp-scan --localnet"), discovery_text.index("nmap -sn"))
    self.assertEqual(decision_for_unconfirmed_start, "deny")
    self.assertEqual(decision_for_follow_up_flow_step, "allow")
```

The scenario must use the real `scripts/approval-gate.py` subprocess, not a reimplementation of its rules.

- [ ] **Step 2: Run the combined-flow test to verify it fails**

Run: `python3 -m unittest tests.test_p2_scenario_harness tests.test_approval_gate -v`
Expected: failure because the harness does not yet assert the full discovery-to-confirmation path as one scenario.

- [ ] **Step 3: Wire the harness to the real gate script and existing docs**

Load `tools/integrations/_discovery.md`, `tools/integrations/_guide.md`, and `scripts/approval-gate.py` directly inside the scenario runner. Keep `tests/test_approval_gate.py` as a low-level unit suite for the hook boundary, but trim any duplication only after the scenario harness passes with the same behavior.

- [ ] **Step 4: Re-run the combined-flow test**

Run: `python3 -m unittest tests.test_p2_scenario_harness tests.test_approval_gate -v`
Expected: pass once the scenario harness proves discovery-first routing, ordered fallback, and confirmation-gated mutation together.

**Phase verification:** a single scenario now proves the policy path end to end without a live HA dependency or duplicated gate logic.

---

## Phase 3: Automation Step 4 contract

This phase addresses P4. It makes the harness prove that the best-practices pack is loaded only when drafting automation JSON and remains advisory.

### Task 4: Add the named automation drafting scenario and keep the pack boundary explicit

**Files:**
- Modify: `tests/test_p2_scenario_harness.py`
- Modify: `tests/test_automation_docs.py`
- Create: `tests/fixtures/p2_scenario_harness/automation-step4.json`

- [ ] **Step 1: Write the failing automation scenario test**

The scenario should check that `tools/automations/_guide.md` routes the pack only at Step 4 and that `tools/ha-best-practices/` stays advisory rather than replacing `CLAUDE.md` authority.

```python
def test_automation_step4_loads_pack_only_when_drafting(self) -> None:
    self.assertIn("Step 4", guide_text)
    self.assertIn("tools/ha-best-practices/", guide_text)
    self.assertIn("advisory", guide_text.lower())
    self.assertIn("CLAUDE.md", tools_router_text)
```

- [ ] **Step 2: Run the automation scenario test to verify it fails**

Run: `python3 -m unittest tests.test_p2_scenario_harness tests.test_automation_docs -v`
Expected: failure because the harness has not yet asserted the Step 4 transition as a scenario boundary.

- [ ] **Step 3: Implement the Step 4 scenario**

Load the live automation guide, the vendored best-practices pack, and the router text in one scenario. The scenario should distinguish:

1. a general automation request that must not preload the pack, and
2. the drafting step where the pack becomes available.

Keep `tests/test_automation_docs.py` focused on pack existence and provenance, and let the scenario harness own the Step 4 behavior assertion.

- [ ] **Step 4: Re-run the automation scenario test**

Run: `python3 -m unittest tests.test_p2_scenario_harness tests.test_automation_docs -v`
Expected: pass once the scenario explicitly reaches Step 4 and confirms the pack stays advisory.

**Phase verification:** the harness now covers the automation-drafting boundary directly instead of relying only on a pack-existence doc test.

---

## Phase 4: Single command and validation artifact

This phase addresses P5. It records one authoritative harness command and produces the validation artifact that future contributors can follow.

### Task 5: Write the validation report and wire the RDW metadata to the harness command

**Files:**
- Create: `docs/p2-scenario-harness/validation-report.md`
- Modify: `docs/p2-scenario-harness/rdw-state.json`
- Modify: `tests/test_integrations_docs.py`

- [ ] **Step 1: Write the failing validation-report test**

Add a check that the report documents the command and the scenario names exactly:

```python
def test_validation_report_records_the_harness_command(self) -> None:
    report = (REPO_ROOT / "docs" / "p2-scenario-harness" / "validation-report.md").read_text()
    self.assertIn("python3 -m unittest tests.test_p2_scenario_harness -v", report)
    self.assertIn("discovery-routing", report)
    self.assertIn("confirmation-boundary", report)
    self.assertIn("automation-step4", report)
```

- [ ] **Step 2: Run the full harness-focused suite to verify it fails**

Run: `python3 -m unittest tests.test_p2_scenario_harness tests.test_approval_gate tests.test_automation_docs tests.test_integrations_docs -v`
Expected: failure because the report and RDW metadata do not yet exist.

- [ ] **Step 3: Create the validation report and update the workflow metadata**

Record the one recommended command in `docs/p2-scenario-harness/validation-report.md`, list the scenarios it covers, and capture the result of running the harness. Update `docs/p2-scenario-harness/rdw-state.json` so the `plan_doc` and `validation_report` fields point at the new plan and report.

- [ ] **Step 4: Re-run the full harness-focused suite**

Run: `python3 -m unittest tests.test_p2_scenario_harness tests.test_approval_gate tests.test_automation_docs tests.test_integrations_docs -v`
Expected: pass once the report records the command, the scenarios are named explicitly, and the RDW metadata points at the right files.

**Phase verification:** the repo has one clear harness command, one validation artifact, and workflow metadata that points future readers at the same path.

---

## Coverage Check

- P1 is covered by Task 1, which creates the dedicated deterministic harness entrypoint under `tests/`.
- P3 is covered by Task 2, which adds the documented fixture schema and both positive and negative fixture shapes under `tests/fixtures/p2_scenario_harness/`.
- P2 is covered by Task 3, which proves discovery-first routing, ordered fallback, and confirmation-gated mutation together in one scenario instead of only in isolated tests.
- P4 is covered by Task 4, which adds the automation drafting scenario and explicitly checks the Step 4 load boundary for `tools/ha-best-practices/`.
- P5 is covered by Task 5, which writes the validation report, records the single command, and updates the RDW metadata to point at the harness artifacts.

## Self-Check

- All five findings map to concrete tasks above.
- Every phase has a verification command and expected result.
- No placeholders such as `TBD`, `TODO`, or “write tests for the above” remain.
- File paths are explicit and consistent across the file structure, tasks, and verification sections.
- The plan respects the Intent ordering: regression confidence first, deterministic/stable execution second, low-maintenance fixture schema third, runtime realism intentionally not expanded beyond repo-local subprocesses.
