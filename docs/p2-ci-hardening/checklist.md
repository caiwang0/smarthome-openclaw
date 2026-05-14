# P2 CI Improvement Checklist

- [x] Extract approval rules from `scripts/approval-gate.py` into a small shared policy module.
- [x] Keep `scripts/approval-gate.py` as a thin wrapper around that policy.
- [x] Add focused unit tests for the policy rules directly.
- [x] Narrow `tests/test_approval_gate.py` to wrapper behavior only.
- [x] Make `tests/test_p2_scenario_harness.py` actually execute `confirmation-boundary`.
- [x] Keep `discovery-routing` and `automation-step4`, but make fixture expectations drive assertions more directly where useful.
- [x] Update `docs/p2-scenario-harness/validation-report.md` so it matches real harness coverage exactly.
- [x] Re-run the focused suites and confirm both the standalone harness command and the broader suite pass.
- [ ] Optional cleanup: reduce doc-string assertions for enforceable rules that are now covered by code.
