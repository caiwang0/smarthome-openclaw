# P2 CI Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the approval-gate policy a single executable source of truth and make the standalone P2 harness command exercise exactly the scenarios it claims.

**Architecture:** Split the approval decision logic into a small repo-local policy module imported by the existing wrapper script. Cover policy decisions directly with unit tests, keep wrapper tests focused on subprocess behavior, then tighten the scenario harness so each fixture-backed scenario proves its documented boundary using the real wrapper path.

**Tech Stack:** Python 3, `unittest`, repo-local fixture JSON, markdown validation docs

---

### Task 1: Extract the approval policy and cover it directly

**Files:**
- Create: `scripts/approval_gate_policy.py`
- Modify: `scripts/approval-gate.py`
- Create: `tests/test_approval_gate_policy.py`
- Modify: `tests/test_approval_gate.py`

- [ ] **Step 1: Write failing policy tests**

Add direct unit tests for:
- denied new config-flow start without explicit confirmation
- allowed confirmed start
- allowed follow-up config-flow step with `flow_id`
- allowed passive/non-gated tool
- confirmation parsing boundaries and transcript extraction edge cases

- [ ] **Step 2: Run policy tests to verify they fail**

Run: `python3 -m unittest tests.test_approval_gate_policy -v`
Expected: FAIL because the shared policy module does not exist yet.

- [ ] **Step 3: Implement the shared policy module and thin wrapper**

Move gated-tool constants and decision helpers into `scripts/approval_gate_policy.py`, keep `scripts/approval-gate.py` responsible for stdin/stdout hook I/O only, and have wrapper tests validate subprocess behavior and fail-open handling.

- [ ] **Step 4: Run focused approval-gate tests**

Run: `python3 -m unittest tests.test_approval_gate_policy tests.test_approval_gate -v`
Expected: PASS

### Task 2: Make the scenario harness execute its claimed boundaries

**Files:**
- Modify: `tests/test_p2_scenario_harness.py`
- Modify: `docs/p2-scenario-harness/validation-report.md`
- Modify: `tests/test_automation_docs.py` or `tests/test_integrations_docs.py` only if obsolete doc-string assertions need trimming

- [ ] **Step 1: Write failing harness assertions**

Add a behavior test that loads `confirmation-boundary.json`, executes both tool runs through the real `scripts/approval-gate.py`, and asserts outcomes from the fixture’s `expect` values. Tighten `discovery-routing` and `automation-step4` to read expected values from fixtures where that improves drift detection.

- [ ] **Step 2: Run the standalone harness suite to verify the new assertions fail or expose the current gap**

Run: `python3 -m unittest tests.test_p2_scenario_harness -v`
Expected: FAIL until the harness truly exercises `confirmation-boundary` and the docs align with real coverage.

- [ ] **Step 3: Implement the harness/doc updates**

Refactor the harness tests for fixture-driven assertions, keep scenario execution local-only, and update `docs/p2-scenario-harness/validation-report.md` to describe the real scenario coverage.

- [ ] **Step 4: Run the required validation commands**

Run:
- `python3 -m unittest tests.test_p2_scenario_harness -v`
- `python3 -m unittest tests.test_p2_scenario_harness tests.test_approval_gate tests.test_automation_docs tests.test_integrations_docs -v`

Expected: PASS for both commands.

### Task 3: Fix the review follow-up gaps in scenario semantics and representative gate coverage

**Files:**
- Modify: `tests/fixtures/p2_scenario_harness/confirmation-boundary.json`
- Modify: `tests/fixtures/p2_scenario_harness/README.md`
- Modify: `tests/test_p2_scenario_harness.py`
- Modify: `docs/p2-scenario-harness/validation-report.md`
- Modify: `tests/test_approval_gate_policy.py`
- Modify: `tests/test_approval_gate.py`
- Modify: `docs/p2-ci-hardening/validation-report.md`

- [ ] **Step 1: Write failing regression expectations for the review findings**

Change `confirmation-boundary` to expect an allowed explicitly confirmed fresh start instead of a `flow_id` follow-up, and add representative non-config-flow deny coverage for the approval gate tests.

- [ ] **Step 2: Run focused tests to expose the current gaps**

Run:
- `python3 -m unittest tests.test_p2_scenario_harness -v`
- `python3 -m unittest tests.test_approval_gate_policy tests.test_approval_gate -v`

Expected:
- the harness suite fails until `confirmation-boundary` stops using the follow-up exemption as its positive path
- the approval-gate suites pass once the new representative deny coverage is added, because that finding is a coverage gap rather than a behavior bug

- [ ] **Step 3: Update fixtures, tests, and docs**

Make `confirmation-boundary` a fresh-start confirmation scenario, keep the follow-up exemption coverage in `discovery-routing`, restore representative non-config-flow deny coverage in policy and wrapper tests, and align both validation reports with the real boundaries.

- [ ] **Step 4: Re-run the required suites and refresh validation evidence**

Run:
- `python3 -m unittest tests.test_p2_scenario_harness -v`
- `python3 -m unittest tests.test_approval_gate_policy tests.test_approval_gate -v`
- `python3 -m unittest tests.test_p2_scenario_harness tests.test_approval_gate tests.test_automation_docs tests.test_integrations_docs -v`

Expected: PASS for all commands.
