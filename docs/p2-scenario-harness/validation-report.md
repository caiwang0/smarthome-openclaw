# P2 Scenario Harness Validation Report

**Date:** 2026-04-20
**Scope:** Deterministic, no-HA validation of the P2 scenario harness

## Recommended Command

```bash
python3 -m unittest tests.test_p2_scenario_harness -v
```

## Scenarios Covered

- `discovery-routing`
- `confirmation-boundary`
- `automation-step4`

## Validation Result

**PASS**

Fresh run on 2026-04-20:

- 6 tests executed
- 0 failures
- 0 errors

## Notes

This harness is intentionally deterministic. It exercises the repo-local P2 policy path without a live Home Assistant instance and uses the real `scripts/approval-gate.py` subprocess plus markdown docs under `tools/` as inputs.

Behavior coverage in the standalone harness suite is:

- `discovery-routing`: executes the read-only discovery allow path, the denied config-flow start, and the allowed follow-up exemption path for an in-progress config flow.
- `confirmation-boundary`: executes the denied config-flow start and the allowed explicitly confirmed fresh config-flow start using the fixture-defined transcripts.
- `automation-step4`: verifies the Step 4 document boundary and advisory pack-loading contract from the fixture-defined expectations.
