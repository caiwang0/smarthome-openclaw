# P1 First-Win Setup and Discovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn setup into one confirmed first-win path, with passive-first discovery, stable fingerprint matching, and explicit confirmation before any new integration/config flow or device addition. Scope stays on checklist items 5-9 only, excluding paused item 9a and any HACS pre-install work.

**Architecture:** Keep the docs as the contract: `CLAUDE.md` defines readiness, `tools/setup.md` defines the terminal first-win path, `tools/integrations/_discovery.md` gathers candidates read-only, and `tools/integrations/_guide.md` only starts mutation flows after the user confirms a candidate. The approval hook remains the enforcement layer for persistent actions; tests lock the text and hook contract so the flow cannot regress to a “connected but empty” success state.

**Tech Stack:** Markdown docs, Markdown fingerprint records with a shared key layout, Python 3 `unittest`/`pytest`, `.claude/settings.json`, `scripts/approval-gate.py`, and the existing ha-mcp tool surface.

---

## File Structure
- `CLAUDE.md` - add the fourth first-run readiness check for zero device-backed, non-system entities.
- `tools/setup.md` - replace the empty-system success case with a first-win terminal path and remove the generic next-steps menu.
- `tools/integrations/_guide.md` - insert discovery-first handoff and explicit confirmation before starting any new config flow.
- `tools/integrations/_discovery.md` - new read-only discovery workflow with passive-first ordering and active fallback only when needed.
- `tools/integrations/fingerprints/xiaomi.md` - new vendor fingerprint record.
- `tools/integrations/fingerprints/hue.md` - new vendor fingerprint record.
- `tools/integrations/fingerprints/shelly.md` - new vendor fingerprint record.
- `tools/integrations/fingerprints/esphome.md` - new vendor fingerprint record.
- `tools/integrations/fingerprints/broadlink.md` - new vendor fingerprint record.
- `.claude/settings.json` - add `ha_config_entries_flow` to the approval matcher.
- `scripts/approval-gate.py` - enforce explicit confirmation for config-flow starts while keeping passive discovery un-gated.
- `tests/test_setup_docs.py` - extend the existing setup-doc regression coverage.
- `tests/test_approval_gate.py` - new hook regression tests.
- `tests/test_integrations_docs.py` - new discovery/fingerprint/guide regression tests.

---

## Phase 1: Safety boundary and readiness invariants

### Task 1: Gate new config-flow starts while preserving passive discovery and existing device-mutation confirmation (Finding P5, checklist item 9)
**Files:**
- Modify: `.claude/settings.json:16-24`
- Modify: `scripts/approval-gate.py:29-176`
- Create: `tests/test_approval_gate.py`

- [ ] **Step 1: Write the failing test**

```python
payload = {
    "tool_name": "mcp__ha-mcp__ha_config_entries_flow",
    "tool_input": {"handler": "hue"},
    "transcript_path": transcript_path,
}
```

Assert that an initial start-flow call is denied when the last user message is not an explicit affirmative, that a follow-up `ha_config_entries_flow` call with `flow_id` passes through, that an already-gated device mutation such as `mcp__ha-mcp__ha_update_device` still requires confirmation, and that `mcp__ha-mcp__ha_config_entries_get` still passes through.

- [ ] **Step 2: Run the test to confirm it fails**

Run: `python3 -m pytest tests/test_approval_gate.py -v`  
Expected: failure because the hook does not yet inspect `tool_input` to distinguish a new flow start from follow-up flow steps, and the regression does not yet lock both sides of the boundary.

- [ ] **Step 3: Update the matcher and gate logic**

Add `ha_config_entries_flow` to the PreToolUse matcher, but update `scripts/approval-gate.py` to inspect `payload["tool_input"]`. Deny only initial flow starts where `tool_name` is `mcp__ha-mcp__ha_config_entries_flow` and `tool_input` does not yet contain a `flow_id`. Allow follow-up submissions, polls, or deletes inside an already-started flow. Keep the current device mutation tools in the gated set so direct device-changing actions still require confirmation. Keep malformed-input fail-open behavior, and do not gate passive reads such as `ha_config_entries_get` or discovery-only searches.

- [ ] **Step 4: Re-run the test to confirm it passes**

Run: `python3 -m pytest tests/test_approval_gate.py -v`  
Expected: pass for confirmed config-flow starts, deny for unconfirmed starts, allow follow-up flow steps with `flow_id`, continue gating direct device mutation tools, and allow passive discovery.

**Phase verification:** the approval hook blocks only new config-flow starts without a fresh affirmative, still gates direct device mutation tools, and leaves follow-up flow steps plus passive discovery allowed. Commit this phase before moving on.

### Task 2: Define empty-system readiness and terminal first-win language (Findings P1 and P4, checklist items 5 and 8)
**Files:**
- Modify: `CLAUDE.md:6-30`
- Modify: `tools/setup.md:247-274`
- Update: `tests/test_setup_docs.py`

- [ ] **Step 1: Write the failing test**

```python
self.assertIn("zero device-backed, non-system entities", claude)
self.assertIn("one verified read or control action", setup)
self.assertNotIn("We can add integrations next.", setup)
self.assertNotIn("Offer Next Steps", setup)
```

- [ ] **Step 2: Run the test to confirm it fails**

Run: `python3 -m pytest tests/test_setup_docs.py -v`  
Expected: failure because the docs still treat the empty system as success and still offer a menu.

- [ ] **Step 3: Update the readiness and terminal-state text**

Add the fourth first-run check to `CLAUDE.md` so the system is not “fully set up” when there are zero device-backed, non-system entities. In `tools/setup.md`, replace the current “connected, but no devices yet” success branch with a first-device handoff that routes into discovery instead of ending on a neutral status. Remove the generic next-steps menu and make the flow stop after the first verified win.

- [ ] **Step 4: Re-run the test to confirm it passes**

Run: `python3 -m pytest tests/test_setup_docs.py -v`  
Expected: pass with the new readiness wording and the terminal first-win state.

**Phase verification:** the setup docs now define the empty-system condition correctly and no longer end with a generic menu. Commit this phase before moving on.

---

## Phase 2: Passive-first discovery entrypoint

### Task 3: Create the read-only discovery flow (Finding P2, checklist item 6)
**Files:**
- Create: `tools/integrations/_discovery.md`
- Modify: `tools/setup.md:247-274`
- Modify: `tools/integrations/_guide.md:5-252`
- Create: `tests/test_integrations_docs.py`

- [ ] **Step 1: Write the failing test**

```python
self.assertIn("passive-first", discovery)
self.assertIn("ha_config_entries_get", discovery)
self.assertIn("ha_search_entities", discovery)
self.assertIn("avahi-browse -atr", discovery)
self.assertIn("ssdp", discovery)
self.assertIn("ip neigh", discovery)
self.assertIn("arp-scan", discovery)
self.assertIn("nmap", discovery)
self.assertIn("explicit user confirmation before any add-device action", discovery)
```

- [ ] **Step 2: Run the test to confirm it fails**

Run: `python3 -m pytest tests/test_integrations_docs.py -v`  
Expected: failure because `_discovery.md` does not exist yet.

- [ ] **Step 3: Add `_discovery.md` with the exact passive-first order**

Use a fixed read-only sequence: existing HA signals first, then mDNS via `avahi-browse -atr`, then SSDP, then `ip neigh`, `arp-scan`, and `nmap` only if passive sources are insufficient. The doc should present candidates as candidates, not as an implied mutation request, and it should end by asking for explicit confirmation before any config-flow start or add-device action.

```markdown
## Discovery Order
1. Read `ha_config_entries_get` and `ha_search_entities`.
2. Probe mDNS with `avahi-browse -atr`.
3. Probe SSDP.
4. If passive signals are insufficient, fall back to `ip neigh`, then `arp-scan`, then `nmap`.
5. Present candidates and wait for explicit confirmation before any config-flow start or add-device action.
```

- [ ] **Step 4: Re-run the test to confirm it passes**

Run: `python3 -m pytest tests/test_integrations_docs.py -v`  
Expected: pass once `_discovery.md` exists and the fallback order is explicit.

**Phase verification:** discovery is read-only, passive-first, only falls back to active scans when passive evidence is insufficient, and never crosses into add/config mutation without confirmation. Commit this phase before moving on.

---

## Phase 3: Fingerprint corpus

### Task 4: Add per-vendor Markdown fingerprints and schema checks (Finding P3, checklist item 7)
**Files:**
- Create: `tools/integrations/fingerprints/xiaomi.md`
- Create: `tools/integrations/fingerprints/hue.md`
- Create: `tools/integrations/fingerprints/shelly.md`
- Create: `tools/integrations/fingerprints/esphome.md`
- Create: `tools/integrations/fingerprints/broadlink.md`
- Modify: `tools/integrations/_discovery.md:1-...`
- Update: `tests/test_integrations_docs.py`

- [ ] **Step 1: Write the failing test**

```python
required = {
    "vendor:",
    "integration_domains:",
    "mac_ouis:",
    "mdns_service_types:",
    "ssdp_signatures:",
}
self.assertTrue(all(field in fingerprint_text for field in required))
```

- [ ] **Step 2: Run the test to confirm it fails**

Run: `python3 -m pytest tests/test_integrations_docs.py -v`  
Expected: failure because the fingerprints directory and Markdown corpus do not exist yet.

- [ ] **Step 3: Add the five Markdown files with one shared key layout**

Use the same keys in every file so `_discovery.md` can consume them without vendor-specific parsing. Example shape:

```md
# Shelly

vendor: shelly
integration_domains:
  - shelly
mac_ouis:
  - E8:DB:84
mdns_service_types:
  - _shelly._tcp
ssdp_signatures:
  - Shelly
```

- [ ] **Step 4: Teach `_discovery.md` to glob and consume the Markdown corpus**

Load every `tools/integrations/fingerprints/*.md` file with the same field names and matching rules. Do not introduce per-vendor branching in the discovery doc.

- [ ] **Step 5: Re-run the test to confirm it passes**

Run: `python3 -m pytest tests/test_integrations_docs.py -v`  
Expected: pass with the five vendor files present and the key layout consistent.

**Phase verification:** the discovery doc now has a deterministic fingerprint corpus that matches the checklist artifact shape and uses one shared key layout. Commit this phase before moving on.

---

## Phase 4: First-win setup handoff and integration confirmation boundary

### Task 5: Rewrite the setup end-state and integration handoff (Findings P1 and P5, checklist items 5 and 9)
**Files:**
- Modify: `tools/setup.md:166-274`
- Modify: `tools/integrations/_guide.md:104-252`
- Update: `tests/test_setup_docs.py`
- Update: `tests/test_integrations_docs.py`

- [ ] **Step 1: Write the failing test**

```python
self.assertIn("one new non-system entity", setup)
self.assertIn("explicit user confirmation before any add-device action", discovery)
self.assertIn("explicit user confirmation", guide)
self.assertNotIn("Offer Next Steps", setup)
self.assertNotIn("We can add integrations next.", setup)
```

- [ ] **Step 2: Run the test to confirm it fails**

Run: `python3 -m pytest tests/test_setup_docs.py tests/test_integrations_docs.py -v`  
Expected: failure because the setup guide still ends in a menu, `_discovery.md` does not yet lock the add-device confirmation boundary, and the integration guide still reaches config flows without the new confirmation boundary.

- [ ] **Step 3: Replace the generic setup menu with a first-win terminal path**

Make `tools/setup.md` stop after the first successful path: one new non-system entity, one verified read or control action, then done. Do not chain into extra integrations or a “what next” menu.

- [ ] **Step 4: Require explicit confirmation before any new config flow starts**

Update `tools/integrations/_guide.md` so passive discovery candidates are shown first and the actual `ha_config_entries_flow` start happens only after the user confirms the chosen candidate. In both `_discovery.md` and `_guide.md`, state explicitly that selecting a discovered device candidate also requires explicit user confirmation before any add-device action is attempted. Leave the paused item 9a / HACS pre-install branch untouched.

- [ ] **Step 5: Re-run the tests to confirm they pass**

Run: `python3 -m pytest tests/test_setup_docs.py tests/test_integrations_docs.py -v`  
Expected: pass with the new terminal setup state and the explicit confirmation boundary.

**Phase verification:** the setup flow now ends after the first verified win, and neither integration starts nor add-device actions can begin mutation without user confirmation. Commit this phase before moving on.

---

## Phase 5: Regression pass

### Task 6: Lock the contract with focused test coverage
**Files:**
- Modify: `tests/test_setup_docs.py`
- Create: `tests/test_approval_gate.py`
- Create: `tests/test_integrations_docs.py`

- [ ] **Step 1: Consolidate the setup assertions**

Keep the existing setup-doc checks, but replace the old empty-system success language with assertions for the new readiness phrase, discovery handoff, and terminal first-win state.

- [ ] **Step 2: Keep the hook regression narrow**

Ensure the gate tests only prove the intended boundary: new `ha_config_entries_flow` starts require a fresh affirmative, existing direct device mutation tools remain gated, and `ha_config_entries_get` plus other passive discovery reads remain allowed.

- [ ] **Step 3: Keep the discovery regression broad enough to catch drift**

Assert that `_discovery.md` still contains passive-first ordering, active fallback only as a last resort, and explicit confirmation language before any config-flow or add-device mutation steps.

- [ ] **Step 4: Run the full focused suite**

Run: `python3 -m pytest tests/test_setup_docs.py tests/test_approval_gate.py tests/test_integrations_docs.py -v`  
Expected: all pass.

**Phase verification:** the repo now has tests covering the safety boundary, the first-run readiness gate, passive-first discovery, the add-device confirmation boundary, and the fingerprint corpus.

---

## Coverage Matrix
| Finding | Phase / Task(s) |
|---|---|
| P1: setup stops before a first device success path | Phase 1 Task 2, Phase 4 Task 5 |
| P2: no passive-first discovery path | Phase 2 Task 3 |
| P3: no fingerprint dataset | Phase 3 Task 4 |
| P4: empty Home Assistant counts as ready | Phase 1 Task 2 |
| P5: approval boundary is underspecified | Phase 1 Task 1, Phase 4 Task 5 |

Blocker note: none identified; the P1-only rollout appears feasible without touching item 9a or widening into P2/P3.
