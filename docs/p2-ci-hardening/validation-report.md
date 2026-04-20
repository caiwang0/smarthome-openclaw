# Validation Report

**Date:** 2026-04-20
**Issue document:** `docs/p2-ci-hardening/issue.md`
**Total findings:** 5
**Passed:** 5 | **Failed:** 0 | **Skipped:** 0

## Results

### P1: Approval policy logic is embedded in the wrapper script - PASS
- [x] Shared policy module extracted.
  Evidence: `scripts/approval_gate_policy.py` now contains the gated-tool list, transcript parsing, confirmation matching, follow-up config-flow check, denial-reason builder, and `evaluate_payload()`. `scripts/approval-gate.py` now handles only hook stdin/stdout and delegates decisions to the policy module.
- [x] Focused unit tests exercise the approval policy directly.
  Evidence: Ran `python3 -m unittest tests.test_approval_gate_policy tests.test_approval_gate -v` on 2026-04-20. Result: 13 tests ran, 0 failures, 0 errors. Direct policy tests cover denied starts, confirmed starts, follow-up config-flow allowance, passive tools, representative device-mutation denial, transcript parsing, and confirmation-length boundaries.
- [x] Wrapper tests cover subprocess behavior only.
  Evidence: The same 13-test run includes 6 wrapper tests that verify structured deny output, silent allow paths, representative device-mutation denial, and malformed-input fail-open behavior through the real `scripts/approval-gate.py` entrypoint.

### P2: The standalone harness suite does not execute `confirmation-boundary` - PASS
- [x] `tests/test_p2_scenario_harness.py` executes `confirmation-boundary` through the real wrapper.
  Evidence: Ran `python3 -m unittest tests.test_p2_scenario_harness -v` on 2026-04-20. Result: 6 tests ran, 0 failures, 0 errors. `test_confirmation_boundary_executes_fixture_behavior` executes a denied fresh start and an allowed explicitly confirmed fresh start via `scripts/approval-gate.py`.
- [x] Fixture expectations drive scenario assertions directly where useful.
  Evidence: `confirmation-boundary.json` now declares `denied_start`, `confirmed_start`, `denied_transcript`, and `confirmed_transcript`; the harness test consumes those keys directly and asserts that the positive path is a fresh start without `flow_id`. `discovery-routing` continues to cover the allowed follow-up exemption, and `automation-step4` continues to assert fixture-defined expectations where applicable.
- [x] The harness remains deterministic and local-only.
  Evidence: The standalone harness run succeeded using repo-local fixture JSON, repo-local markdown docs, and the local `scripts/approval-gate.py` subprocess only. No live Home Assistant instance, MCP server, or network dependency was required.

### P3: Harness validation docs overstate current coverage - PASS
- [x] `docs/p2-scenario-harness/validation-report.md` matches real harness coverage.
  Evidence: The report now records 6 executed tests and describes the exact behavior coverage for `discovery-routing`, `confirmation-boundary`, and `automation-step4`, including the distinction between the follow-up exemption and a confirmed fresh start.
- [x] Fresh CI-hardening validation evidence is recorded.
  Evidence: Ran `python3 -m unittest tests.test_p2_scenario_harness tests.test_approval_gate tests.test_automation_docs tests.test_integrations_docs -v` on 2026-04-20. Result: 17 tests ran, 0 failures, 0 errors.

### P4: `confirmation-boundary` still proves the follow-up exemption instead of fresh confirmation - PASS
- [x] `confirmation-boundary` now executes a denied fresh config-flow start and an allowed explicitly confirmed fresh config-flow start.
  Evidence: Ran `python3 -m unittest tests.test_p2_scenario_harness -v` on 2026-04-20. Result: 6 tests ran, 0 failures, 0 errors. `test_confirmation_boundary_executes_fixture_behavior` now asserts that the allowed path omits `flow_id` and succeeds only because the transcript is affirmative.
- [x] `discovery-routing` remains the scenario that covers the allowed follow-up exemption.
  Evidence: The same harness run still executes `discovery-routing` with a `flow_id` follow-up tool run and asserts the allowed follow-up expectation separately from `confirmation-boundary`.
- [x] Harness and validation docs describe those boundaries accurately.
  Evidence: `tests/fixtures/p2_scenario_harness/README.md`, `docs/p2-scenario-harness/validation-report.md`, and this report now distinguish explicitly confirmed fresh starts from the follow-up exemption path.

### P5: Representative non-config-flow gated coverage regressed during the refactor - PASS
- [x] The direct policy tests include a denied non-config-flow gated tool.
  Evidence: Ran `python3 -m unittest tests.test_approval_gate_policy tests.test_approval_gate -v` on 2026-04-20. Result: 13 tests ran, 0 failures, 0 errors. `test_denies_device_mutation_without_confirmation` exercises `mcp__ha-mcp__ha_update_device` at the policy layer.
- [x] The wrapper subprocess tests include a denied non-config-flow gated tool.
  Evidence: The same 13-test run includes `test_wrapper_denies_device_mutation_without_confirmation`, which verifies the real wrapper emits a deny decision for `ha_update_device`.
- [x] The approval-gate validation report records the refreshed coverage evidence.
  Evidence: This validation report and `rdw-state.json` now record the expanded 13-test approval-gate coverage alongside the required harness and broader suite runs.

## Accepted Residual Risks

None.

## New Issues Discovered

None.

## Verdict

ALL PASS for findings P1-P5. The approval policy remains a single executable source of truth, `confirmation-boundary` now proves an explicitly confirmed fresh start instead of a `flow_id` exemption, representative non-config-flow gated coverage is restored, and the validation docs match the tested boundaries.
