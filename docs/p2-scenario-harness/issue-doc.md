# P2 Deterministic Scenario Harness Issue Document

**Date:** 2026-04-20
**Scope:** Add a deterministic, no-HA scenario harness for the P2 policy path so the repo can test discovery routing, confirmation boundaries, fallback ordering, and automation best-practices loading as one coherent regression surface
**Analyst:** Codex via review-driven-workflow

## Summary

This audit checked how the repo currently validates the P2 structural-cleanup behavior. Five findings remain: there is no dedicated scenario harness, the current coverage is split across isolated tests rather than end-to-end policy scenarios, there is no reusable fixture schema for discovery/confirmation flows, the automation-drafting guidance is not exercised in a scenario test, and there is no single command or validation artifact for the new harness.

Overall severity is medium. The core risk is not production breakage; it is that the repo can drift away from the intended P2 conversation behavior while still passing narrow doc and hook unit tests.

## Intent

**Goal:** Add a stable deterministic scenario harness that gives fast, CI-friendly evidence that the P2 behavior rules hold together as a single flow without requiring a live Home Assistant instance.

**Priority ranking:** regression confidence for P2 policy behavior > deterministic/stable test execution > low maintenance cost > maximizing runtime realism

**Decision boundaries:** The agent may add repo-local fixtures, test utilities, and lightweight helper scripts; may extend existing tests when that reduces duplication; may document a single recommended command for running the scenario harness. The agent must not expand this workflow into a live Home Assistant smoke harness or a full conversation runner.

**Stop rules:** Stop if the harness design requires a live HA instance to prove basic P2 behavior; stop if a proposed scenario runner duplicates `scripts/approval-gate.py` logic instead of exercising the real script; stop if the scope expands into a generic chat-agent simulation layer rather than the specific P2 policy path.

## Findings

### P1: The repo has no dedicated deterministic scenario harness for the P2 policy path

**Severity:** Medium
**Category:** Test infrastructure
**Affected components:** `tests/`, P2 validation workflow, repo-local test entrypoints

**Description:** The current repo contains doc assertions and hook unit tests, but no scenario-level harness that can replay a named P2 path from discovery through confirmation boundaries and automation draft guidance.

**Impact:** The P2 behavior rules can regress independently while the narrower unit/doc tests still pass, because no single test surface models the intended path as one scenario.

**Success criteria:**
- [ ] A dedicated scenario harness test file exists under `tests/`.
- [ ] The harness executes named P2 scenarios from structured fixtures rather than ad hoc inline strings only.
- [ ] Running the harness verifies more than one subsystem in the same scenario path (for example discovery ordering plus approval-gate behavior).

---

### P2: Current P2 coverage is fragmented across isolated tests instead of cross-scenario policy assertions

**Severity:** Medium
**Category:** Coverage gaps
**Affected components:** `tests/test_integrations_docs.py`, `tests/test_approval_gate.py`, `tests/test_automation_docs.py`

**Description:** The current tests validate the discovery docs, approval gate, and automation pack separately. That proves each piece exists, but it does not prove that the expected P2 user journey routes through those pieces in the right sequence.

**Impact:** A future change could preserve all the individual assertions while breaking the combined behavior that the user actually cares about.

**Success criteria:**
- [ ] At least one scenario asserts discovery-first routing, ordered fallback behavior, and confirmation-gated mutation as one coherent flow.
- [ ] At least one scenario asserts that automation drafting reaches the best-practices pack at Step 4 rather than as a global always-on dependency.
- [ ] Existing narrow tests remain in place or are replaced only if the scenario harness fully subsumes their coverage.

---

### P3: There is no reusable fixture schema for P2 discovery, confirmation, and automation-drafting scenarios

**Severity:** Medium
**Category:** Test maintainability
**Affected components:** `tests/fixtures/` or equivalent new fixture location

**Description:** The repo has no structured fixture format for representing discovery evidence, fallback constraints, approval-gate payloads, user confirmations, or expected scenario outcomes. Without that, scenario tests are likely to become brittle one-off scripts.

**Impact:** The first scenario test might pass, but adding or maintaining scenarios later would be expensive and inconsistent.

**Success criteria:**
- [ ] Scenario fixtures live in a dedicated fixture directory with a documented schema.
- [ ] The schema can represent both positive and negative paths (for example: command missing, permission denied, no confirmation, confirmed follow-up).
- [ ] New P2 scenarios can be added without rewriting the harness logic itself.

---

### P4: The automation best-practices Step 4 contract is not exercised in a scenario-level test

**Severity:** Medium
**Category:** Regression safety
**Affected components:** `tools/automations/_guide.md`, `tools/ha-best-practices/`, scenario harness coverage

**Description:** The current automation-doc test confirms the pack exists and is referenced, but it does not model an automation-drafting scenario that explicitly reaches Step 4 and proves the pack is loaded only at that drafting point.

**Impact:** The repo can drift toward always-on loading or lose the draft-only boundary without a scenario test catching that behavior change directly.

**Success criteria:**
- [ ] A named automation scenario checks the Step 4 transition explicitly.
- [ ] The scenario distinguishes “draft stage” behavior from “general automation request” behavior.
- [ ] The scenario asserts that the best-practices pack remains advisory and does not replace `CLAUDE.md` authority.

---

### P5: The repo lacks a single documented command and validation artifact for the deterministic P2 scenario harness

**Severity:** Low
**Category:** Developer workflow
**Affected components:** validation docs, test invocation surface, RDW artifacts

**Description:** Even after the harness is added, it needs one clear invocation path and a validation artifact that records how it proves the narrowed P2 behavior. The current P2 validation report covers the structural cleanup work, not the new scenario harness.

**Impact:** Future contributors may not know which command is authoritative for P2 scenario validation, or may skip it in favor of the older narrower tests.

**Success criteria:**
- [ ] There is one clear command for running the deterministic P2 harness, either standalone or as a focused unittest module.
- [ ] The workflow produces a validation report that records the harness command and the scenarios it covers.
- [ ] The live docs/checklist point at the new validation path where appropriate.

## Accepted Residual Risks

- This harness will not prove real Home Assistant config-flow or network behavior; that remains an accepted residual risk for this workflow because the user chose the deterministic no-HA path.
- The harness will simulate the P2 policy path, not a full OpenClaw/Codex conversation runner.

## Dependencies Between Findings

- P1 blocks P2 because there must be a dedicated harness before the policy flow can be asserted coherently.
- P3 supports P1 and P2 because maintainable fixtures are required to express discovery and approval variants without duplicating test logic.
- P4 depends on the harness structure from P1/P3 so the Step 4 automation boundary can be modeled consistently.
- P5 depends on the implementation and validation of P1-P4 so the documented command and report reflect the real harness shape.
