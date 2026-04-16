# Validation Report

**Date:** 2026-04-15
**Issue document:** `docs/rdw-p1-5-9-issue-doc.md`
**Total findings:** 5
**Passed:** 5 | **Failed:** 0 | **Skipped:** 0

## Validation Matrix

| ID | Title | Checks | Result |
|---|---|---|---|
| P1 | Setup flow ends on a first verified win | `nl -ba tools/setup.md \| sed -n '240,320p'`; `python3 -m pytest tests/test_setup_docs.py tests/test_integrations_docs.py -v` | PASS |
| P2 | Passive-first discovery exists | `nl -ba tools/integrations/_discovery.md \| sed -n '1,200p'`; `python3 -m pytest tests/test_setup_docs.py tests/test_integrations_docs.py -v` | PASS |
| P3 | Fingerprint corpus exists and is uniform | `find tools/integrations/fingerprints -maxdepth 1 -type f \| sort \| xargs -r -n 1 basename`; `nl -ba tools/integrations/_discovery.md \| sed -n '1,200p'`; `python3 -m pytest tests/test_setup_docs.py tests/test_integrations_docs.py -v` | PASS |
| P4 | Empty system no longer counts as ready | `nl -ba CLAUDE.md \| sed -n '1,120p'`; `nl -ba tools/setup.md \| sed -n '240,320p'`; `python3 -m pytest tests/test_setup_docs.py tests/test_integrations_docs.py -v` | PASS |
| P5 | Approval boundary stays explicit and enforced | `nl -ba .claude/settings.json \| sed -n '1,220p'`; `nl -ba scripts/approval-gate.py \| sed -n '1,220p'`; `nl -ba tools/integrations/_guide.md \| sed -n '1,220p'`; `nl -ba tools/integrations/_discovery.md \| sed -n '1,200p'`; `python3 -m pytest tests/test_setup_docs.py tests/test_approval_gate.py tests/test_integrations_docs.py -v` | PASS |

## Results

### P1: Setup flow stops before a first device success path - PASS
- `tools/setup.md:247-266` now defines setup completion as a first verified win, not a neutral connection status.
- `tools/setup.md:260-262` requires one new non-system entity that is device-backed and not in the baseline.
- `tools/setup.md:261-266` requires one verified read or control action and explicitly says not to offer a generic next-steps menu after the first win.

### P2: No passive-first discovery path exists before asking the user what to connect - PASS
- `tools/integrations/_discovery.md:7-19` defines the passive-first order: existing HA signals, mDNS, SSDP, then active fallback only if passive evidence is insufficient.
- `tools/integrations/_discovery.md:18-26` frames output as candidates and keeps mutation out of the discovery entrypoint.
- Focused doc regression output: `3 passed in 0.02s`.

### P3: Discovery has no consistent fingerprint dataset to consume - PASS
- Fingerprint corpus listing shows the required vendor files:

```text
broadlink.md
esphome.md
hue.md
shelly.md
xiaomi.md
```

- `tools/integrations/_discovery.md:28-40` instructs the agent to load `tools/integrations/fingerprints/*.md` and consume the shared fields `vendor`, `integration_domains`, `mac_ouis`, `mdns_service_types`, and `ssdp_signatures`.
- Focused doc regression output: `3 passed in 0.02s`.

### P4: First-run readiness treats an empty Home Assistant instance as fully set up - PASS
- `CLAUDE.md:8-32` now defines four first-run checks, including the zero-device-backed, non-system-entity condition.
- `tools/setup.md:258-259` routes the no-device case directly into the discovery flow instead of treating it as a finished setup state.
- Focused doc regression output: `3 passed in 0.02s`.

### P5: Approval boundary is not explicit enough for post-discovery integration and device actions - PASS
- `.claude/settings.json:17-24` includes `ha_config_entries_flow` in the PreToolUse matcher.
- `scripts/approval-gate.py:31-53` keeps mutation tools gated, and `scripts/approval-gate.py:141-150` allows follow-up config-flow steps with `flow_id` so only new starts require fresh confirmation.
- `tools/integrations/_discovery.md:18-26` and `tools/integrations/_guide.md:7-11,142-147` distinguish passive discovery from mutation and require explicit confirmation before config-flow starts or add-device actions.
- Full focused regression output:

```text
============================= test session starts ==============================
collected 9 items
tests/test_setup_docs.py::SetupDocsTests::test_setup_docs_handle_seeded_and_manual_readiness_paths PASSED
tests/test_approval_gate.py::ApprovalGateTests::test_confirmed_new_config_flow_start_is_allowed PASSED
tests/test_approval_gate.py::ApprovalGateTests::test_device_mutation_still_requires_confirmation PASSED
tests/test_approval_gate.py::ApprovalGateTests::test_follow_up_config_flow_step_is_allowed PASSED
tests/test_approval_gate.py::ApprovalGateTests::test_malformed_input_fails_open PASSED
tests/test_approval_gate.py::ApprovalGateTests::test_new_config_flow_start_requires_confirmation PASSED
tests/test_approval_gate.py::ApprovalGateTests::test_passive_config_entries_get_is_allowed PASSED
tests/test_integrations_docs.py::IntegrationDocsTests::test_discovery_entrypoint_and_confirmation_boundary PASSED
tests/test_integrations_docs.py::IntegrationDocsTests::test_fingerprint_corpus_schema_and_discovery_contract PASSED
============================== 9 passed in 0.24s ===============================
```

## Accepted Residual Risks

- Checklist item `9a` remains paused and excluded from this workflow.
- P2/P3 cleanup outside checklist items 5-9 remains out of scope; validation found no dependency that forced a scope expansion.

## New Issues Discovered

- None during final validation.

## Verdict

All 5 findings from `docs/rdw-p1-5-9-issue-doc.md` validated with concrete evidence. P1 items 5-9 are complete within the requested scope, with paused item `9a` still excluded.
