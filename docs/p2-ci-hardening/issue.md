# P2 CI Hardening Issue Document

**Date:** 2026-04-20
**Scope:** Approval-gate / P2 scenario harness CI hardening in the local-only test harness
**Analyst:** Codex

## Summary

The approval gate and P2 scenario harness already provide deterministic local-only coverage, but this follow-up cycle surfaced five scoped findings across policy extraction, scenario semantics, representative gate coverage, and validation accuracy. The current issue document tracks the original CI-hardening gaps plus the two review-discovered follow-up gaps that were added after the first code-review pass.

## Intent

**Goal:** Make the approval-gate and P2 harness tests honest, deterministic, and easier to maintain without introducing any Home Assistant, MCP, or network dependency.
**Priority ranking:** Deterministic local behavior > single source of truth for approval policy > minimal diff size > doc cleanup
**Decision boundaries:** I can refactor repo-local Python modules, tighten tests, and update repo-local validation docs. I should not introduce live HA/MCP/LLM dependencies or broaden scope beyond approval-policy / harness hardening.
**Stop rules:** Pause if the refactor would require a packaging change outside this worktree, if focused tests reveal unrelated breakage that changes the scope materially, or if the real approval-gate wrapper cannot stay as the scenario execution path.

## Findings

### P1: Approval policy logic is embedded in the wrapper script

**Severity:** Medium
**Category:** Reliability
**Affected components:** `scripts/approval-gate.py`, `tests/test_approval_gate.py`

**Description:** The gated-tool list, confirmation parsing, transcript extraction, and config-flow follow-up logic currently live inside `scripts/approval-gate.py`. That keeps the standalone hook working, but it prevents focused unit tests from exercising the approval policy directly and makes the wrapper test file carry both policy and subprocess responsibilities.

**Impact:** Approval behavior can drift between what the wrapper script does and what CI tests claim to cover. Failures are harder to localize because the current tests validate policy rules only through subprocess execution.

**Success criteria:**
- [ ] A shared policy module provides the approval-rule decisions used by `scripts/approval-gate.py`.
- [ ] Focused unit tests exercise the approval policy directly without shelling out.
- [ ] `tests/test_approval_gate.py` covers wrapper/subprocess behavior only.

---

### P2: The standalone harness suite does not execute `confirmation-boundary`

**Severity:** Medium
**Category:** Test Coverage
**Affected components:** `tests/test_p2_scenario_harness.py`, `tests/fixtures/p2_scenario_harness/confirmation-boundary.json`

**Description:** The harness fixtures and validation report list `confirmation-boundary` as covered, but the standalone harness suite currently validates only the schema/load path for that fixture. It does not run the real `scripts/approval-gate.py` against that scenario as a behavior test.

**Impact:** The recommended standalone harness command can pass while not actually proving one of the scenarios it claims to cover. That weakens CI confidence and makes the validation doc inaccurate.

**Success criteria:**
- [ ] `tests/test_p2_scenario_harness.py` executes the `confirmation-boundary` fixture through the real approval-gate wrapper.
- [ ] Scenario assertions are driven by fixture expectations where practical, so fixture drift is caught by the behavior tests.
- [ ] The standalone harness command remains deterministic and local-only.

---

### P3: Harness validation docs overstate current coverage

**Severity:** Low
**Category:** Documentation
**Affected components:** `docs/p2-scenario-harness/validation-report.md`, `docs/p2-ci-hardening/validation-report.md`

**Description:** The existing harness validation report says the standalone harness command covers `discovery-routing`, `confirmation-boundary`, and `automation-step4`, but the current suite does not truly execute all three scenarios as behavior tests.

**Impact:** CI documentation can mislead future maintainers about what is enforced by tests versus what is only listed in fixtures or docs.

**Success criteria:**
- [ ] `docs/p2-scenario-harness/validation-report.md` matches real harness coverage exactly.
- [ ] The CI hardening validation report records the focused verification commands and their fresh results.

---

### P4: `confirmation-boundary` still proves the follow-up exemption instead of fresh confirmation

**Severity:** Medium
**Category:** Test Coverage
**Affected components:** `tests/fixtures/p2_scenario_harness/confirmation-boundary.json`, `tests/test_p2_scenario_harness.py`, `docs/p2-scenario-harness/validation-report.md`

**[DISCOVERED DURING IMPLEMENTATION]**

**Description:** The current `confirmation-boundary` fixture names its positive path as confirmation coverage, but that tool run includes `flow_id`. The approval policy allows follow-up config-flow steps before checking transcript confirmation, so the scenario is actually proving the follow-up exemption rather than an explicitly confirmed fresh start.

**Impact:** The standalone harness and validation docs overstate what they prove. A misleading positive-path claim weakens CI trust even though the underlying wrapper behavior is deterministic.

**Success criteria:**
- [ ] `confirmation-boundary` executes a denied fresh config-flow start and an allowed explicitly confirmed fresh config-flow start.
- [ ] `discovery-routing` remains the scenario that covers the allowed follow-up exemption.
- [ ] Harness and validation docs describe those boundaries accurately.

---

### P5: Representative non-config-flow gated coverage regressed during the refactor

**Severity:** Medium
**Category:** Test Coverage
**Affected components:** `tests/test_approval_gate_policy.py`, `tests/test_approval_gate.py`, `scripts/approval_gate_policy.py`

**[DISCOVERED DURING IMPLEMENTATION]**

**Description:** The shared policy still gates device, system, and HACS mutations, but the direct policy tests now focus only on config-flow behavior plus one read-only allow path. The wrapper suite also dropped the old `ha_update_device` deny check.

**Impact:** CI would not catch a regression that accidentally removes representative non-config-flow mutations from `GATED_TOOLS`.

**Success criteria:**
- [ ] The direct policy tests include at least one denied non-config-flow gated tool.
- [ ] The wrapper subprocess tests include at least one denied non-config-flow gated tool.
- [ ] The approval-gate validation report records the refreshed coverage evidence.

## Accepted Residual Risks

None.

## Dependencies Between Findings

- P1 should land before narrowing wrapper tests so the new policy unit tests have a stable shared module to target.
- P2 depends on P1 only insofar as the harness should continue to execute the real wrapper script after the refactor.
- P3 depends on the final post-change test runs from P1 and P2.
- P4 depends on P2 because it refines the scenario semantics after the harness execution gap was first closed.
- P5 depends on P1 because it extends the shared-policy coverage added by the refactor.
