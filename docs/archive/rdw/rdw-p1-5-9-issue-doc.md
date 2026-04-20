# P1 Items 5-9 Issue Document

**Date:** 2026-04-15
**Scope:** `docs/fix-checklist.md` P1 items 5-9 only, explicitly excluding paused item 9a
**Analyst:** Codex

## Summary

Reviewed the current first-run setup, integration guidance, and approval-gate enforcement for the production-facing SmartHub setup flow. The repo currently has five active gaps across checklist items 5-9: the setup flow can end before a first device win, discovery is missing, discovery fingerprints are missing, the first-run gate treats an empty system as ready, and the approval boundary is under-specified for post-discovery mutation paths.

Overall risk is **High** because the current flow can report success before the user controls anything, while the integration guidance still leaves room for autonomous persistent changes if discovery is added without a tighter boundary.

## Intent

**Goal:** Turn the current install/setup flow into a single first-win path that ends only after one real device or integration is connected and verified, without weakening the existing approval-gate safety model.

**Priority ranking:** approval-gate safety model > one first-win completion path > passive-first discovery accuracy > P1-only scope containment > implementation convenience

**Decision boundaries:** passive discovery is allowed without approval; starting a new integration/config flow or adding a device requires explicit user confirmation; the agent may define file formats and routing details needed for P1 items 5-9; the agent may not broaden into P2/P3 cleanup unless a documented dependency makes P1-only delivery impossible.

**Stop rules:** do not implement paused item 9a; do not broaden scope into P2/P3; stop and ask if the current repo structure prevents a clean P1-only rollout; stop and ask if satisfying item 9 would require weakening the existing approval-gate model instead of preserving it.

## Findings

### P1: Setup flow stops before a first device success path (Checklist item 5)

**Severity:** High
**Category:** Onboarding
**Affected components:** `tools/setup.md`

**Description:** The current setup guide ends after Home Assistant and `ha-mcp` connectivity checks. Its terminal state is either "Connected! I found X entities." or "Connected, but no devices yet. We can add integrations next." There is no required completion path that ends only after exactly one integration is added, or one device is added/discovered and connected, with a verified interaction.

**Impact:** Setup can claim success before the user experiences device control. That breaks the intended AHA moment, leaves the user at a menu boundary instead of a finished outcome, and makes downstream "connected but empty" states ambiguous.

**Success criteria:**
- [ ] `tools/setup.md` defines setup completion as exactly one successful first-win path: either one integration is added, or one device is added/discovered and connected.
- [ ] The documented first-win path requires at least one new non-system entity relative to the pre-setup baseline.
- [ ] The documented first-win path requires one verified read or control action against that new entity, and the setup flow stops after the first successful path instead of returning to a menu.

---

### P2: No passive-first discovery path exists before asking the user what to connect (Checklist item 6)

**Severity:** High
**Category:** Discovery
**Affected components:** `tools/setup.md`, `tools/integrations/`

**Description:** The repo does not contain `tools/integrations/_discovery.md`, and the current setup/integration guidance has no standard discovery phase before asking the user to choose or add an integration. There is no documented passive-first method that uses mDNS, SSDP, or existing HA/discovery signals before resorting to active LAN scans.

**Impact:** The agent has to ask blind inventory questions or jump straight into integration setup without evidence. That increases user effort, makes wrong integration choices more likely, and weakens the quality of the first-device routing decision.

**Success criteria:**
- [ ] `tools/integrations/_discovery.md` exists and instructs the agent to use passive-first discovery sources, including existing HA/discovery signals, mDNS via `avahi-browse`, and SSDP, before any active LAN scan.
- [ ] Active scan fallbacks such as `arp-scan`, `nmap`, and `ip neigh` are only used when passive discovery is insufficient, rather than as the default path.
- [ ] Discovery output is presented to the user as candidate devices/integrations instead of a blind "what devices do you own?" prompt.

---

### P3: Discovery has no consistent fingerprint dataset to consume (Checklist item 7)

**Severity:** Medium
**Category:** Discovery Data
**Affected components:** `tools/integrations/`

**Description:** `tools/integrations/` currently contains only `_guide.md`. There is no `fingerprints/` directory, no shared fingerprint schema, and no vendor files covering MAC OUI prefixes, mDNS service types, SSDP signatures, or likely HA integration domains. A discovery skill introduced now would have no deterministic input format to consume.

**Impact:** Discovery matching would be inconsistent across sessions, `_discovery.md` would have to invent its own ad hoc heuristics, and vendor-to-integration recommendations would not be repeatable or maintainable.

**Success criteria:**
- [ ] `tools/integrations/fingerprints/` exists and uses one consistent per-vendor file format consumable by `_discovery.md`.
- [ ] Starter fingerprint files exist for `xiaomi`, `hue`, `shelly`, `esphome`, and `broadlink`.
- [ ] Each fingerprint file contains MAC OUI prefixes, mDNS service types, SSDP signatures, and likely HA integration domains in the same field structure.
- [ ] `_discovery.md` can consume each vendor file using the same field names and matching rules instead of per-file special cases.

---

### P4: First-run readiness treats an empty Home Assistant instance as fully set up (Checklist item 8)

**Severity:** High
**Category:** First-Run Guardrail
**Affected components:** `CLAUDE.md`, `tools/setup.md`

**Description:** `CLAUDE.md` defines only three first-run checks: `.env`, HA reachability, and `ha-mcp` connectivity. After those pass, the setup flow can still end with zero device-backed, non-system entities. The current setup guide acknowledges this case but does not treat it as a failed first-run gate or route into a required first-device flow.

**Impact:** The system can report "ready" when the user still cannot read or control any real device. That creates false-positive setup completion and pushes the product's first useful action into a later, undefined conversation.

**Success criteria:**
- [ ] `CLAUDE.md` includes a fourth first-run check for zero device-backed, non-system entities.
- [ ] The no-device condition is defined as zero device-backed, non-system entities; system entities and helpers do not satisfy readiness.
- [ ] When that check fails, the documented path routes directly into the first-device discovery/integration flow instead of stopping at a neutral status message.

---

### P5: Approval boundary is not explicit enough for post-discovery integration and device actions (Checklist item 9)

**Severity:** High
**Category:** Safety
**Affected components:** `.claude/settings.json`, `scripts/approval-gate.py`, `tools/integrations/_guide.md`

**Description:** The current approval gate only matches a fixed list of destructive `ha-mcp` tools, while `tools/integrations/_guide.md` still describes silent infrastructure work around HACS/custom integration installation and does not define a clean handoff between approval-free passive discovery and approval-required mutation steps. As the first-device flow moves toward discovery-first routing, the safety boundary around starting config flows, enabling integrations, and adding devices is not yet explicit end to end.

**Impact:** A discovery-led setup flow could slide from read-only discovery into persistent configuration changes without an explicit user confirmation checkpoint. That would violate the stated approval-gate model for production-facing setup.

**Success criteria:**
- [ ] The docs and enforcement clearly distinguish passive discovery from mutation: discovery/search/read actions remain approval-free, while starting a new integration/config flow or adding a device/integration requires explicit user confirmation.
- [ ] The approval-gate matcher/script covers the mutation tools used by the first-device flow without gating passive discovery tools.
- [ ] `tools/integrations/_guide.md` and any discovery entrypoint instruct the agent to present discovered candidates first and wait for confirmation before any add/config action.

## Accepted Residual Risks

- Checklist item 9a remains paused and is explicitly excluded from this workflow.
- P2 and P3 cleanup items outside checklist items 5-9 remain out of scope unless a dependency proves P1-only delivery impossible, in which case execution must stop and escalate.

## Dependencies Between Findings

- P2 and P3 jointly provide the discovery capability and fingerprint inputs needed to make P1's first-win setup path deterministic.
- P4 depends on the existence of the P1/P2 flow because the first-run gate needs somewhere concrete to route the user when no devices exist yet.
- P5 constrains the transition from P2 discovery into P1 completion so discovery can stay approval-free while mutation steps remain explicitly confirmed.
