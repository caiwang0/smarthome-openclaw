# Integrations — Lifecycle Harness

Use this orchestration skill after `tools/integrations/_discovery.md` has collected evidence and the user has confirmed which candidate or integration path they want to pursue.

Primary route:

`tools/integrations/_discovery.md` → `tools/integrations/_lifecycle.md` → `tools/integrations/_guide.md`

`tools/integrations/_guide.md` is the config-flow helper used during `CONNECTING`. It is not the entrypoint for discovery or candidate selection.

## State Sequence

`DISCOVERED → IDENTIFIED → INTEGRATION_SELECTED → CONNECTING → CONNECTED → VERIFIED → SKILL_GENERATED`

Move forward only when the current state's exit condition is satisfied. If a state fails, use the failure handling rules below instead of improvising a new path.

## State Rules

### DISCOVERED

- **Entry condition:** `tools/integrations/_discovery.md` produced one or more candidates, or explicitly reported that it found none.
- **Required data:** passive signals, active fallback evidence if used, confidence level, and whether the user has already confirmed a candidate.
- **Allowed actions:** summarize the candidates, explain what evidence supports them, and ask the user which path to pursue.
- **Exit condition:** the user either confirms one candidate / integration path or declines all discovered candidates.
- **Failure handling:** if discovery found nothing, say so plainly, list which passive/active sources were checked, and stop. Do not start a config flow without a confirmed target.

### IDENTIFIED

- **Entry condition:** the user chose a candidate from discovery.
- **Required data:** likely integration domain, likely device or service type, local-vs-cloud expectation, and any prerequisites already known.
- **Allowed actions:** confirm the intended integration domain, call out ambiguity if multiple domains fit, and ask only the minimum clarifying question needed to resolve that ambiguity.
- **Exit condition:** one integration domain is selected for the chosen candidate.
- **Failure handling:** if the evidence does not support a single reasonable integration domain, stop and tell the user what remains ambiguous instead of guessing.

### INTEGRATION_SELECTED

- **Entry condition:** a concrete integration domain is known.
- **Required data:** selected integration domain, whether it is built-in or needs prerequisite install work, and whether the user already approved the mutation step.
- **Allowed actions:** present the integration path, remind the user that discovery was read-only, and ask for explicit confirmation before any config-flow start or add-device action.
- **Exit condition:** the user explicitly confirms that the selected integration should be connected.
- **Failure handling:** if the user has not confirmed, stay in this state. Do not call `ha_config_entries_flow`, do not add a device, and do not perform prerequisite install work.

### CONNECTING

- **Entry condition:** the user explicitly confirmed the selected integration path.
- **Required data:** integration domain, current HA state, and any fields needed by the config or prerequisite flow.
- **Allowed actions:** follow `tools/integrations/_guide.md` for dashboard routing, config-flow walking, OAuth handling, and recovery guidance.
- **Exit condition:** Home Assistant returns a created config entry or equivalent success signal for the selected integration.
- **Failure handling:** use the recovery ladder in `tools/_errors.md` and then return to the current lifecycle state. If the failure changes the user-facing choice set, pause and ask instead of silently switching paths.

### CONNECTED

- **Entry condition:** the integration exists in Home Assistant.
- **Required data:** the baseline entity set from before the integration work, the current entity set, and any newly discovered devices exposed by the config entry.
- **Allowed actions:** inspect entities, compare against the baseline, and identify device-backed, non-system entities that were not present before the connection attempt.
- **Exit condition:** at least one new device-backed, non-system entity is attributable to the selected integration.
- **Failure handling:** if the integration is present but exposes no new qualifying entity, tell the user that the integration connected without producing a first-win device and stop before claiming success.

### VERIFIED

- **Entry condition:** at least one new device-backed, non-system entity exists.
- **Required data:** one concrete read or control action that can be safely verified against the new entity set.
- **Allowed actions:** perform one read or control action and confirm the observed result.
- **Exit condition:** one verified read or control action succeeds against an entity that came from the selected integration path.
- **Failure handling:** if verification fails, report the exact failed step and stay out of `SKILL_GENERATED`. A connected-but-unverified integration is not a completed first win.

### SKILL_GENERATED

- **Entry condition:** the first-win verification succeeded.
- **Required data:** integration domain, connected devices, entity IDs, and any quirks learned during the flow.
- **Allowed actions:** follow the skill auto-generation rules in `TOOLS.md` to update integration/device knowledge files.
- **Exit condition:** repo knowledge reflects the newly connected integration or devices.
- **Failure handling:** if documentation generation cannot be completed immediately, tell the user the integration is connected and verified, then record the missing knowledge-file follow-up explicitly instead of silently dropping it.

## Failure Handling Rules

- Preserve the approval boundary: discovery is read-only; integration selection, config-flow start, and add-device actions require explicit user confirmation.
- When a failure happens in `CONNECTING`, use `tools/_errors.md` first, then return to the lifecycle state that failed.
- When a failure changes which integration path is viable, stop and ask rather than auto-switching to a different integration.
- Do not claim success until the flow reaches `VERIFIED`.
