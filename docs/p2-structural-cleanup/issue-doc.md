# P2 Structural Cleanup Issue Document

**Date:** 2026-04-20
**Scope:** P2 items 10-12 and 13a from `docs/fix-checklist.md`, covering the integration-flow skill architecture, discovery fallback behavior, and the vendored automation best-practices pack
**Analyst:** Codex via review-driven-workflow

## Summary

This audit checked whether the repository structure around the newly landed first-device flow matches the intended P2 follow-up work. Four findings remain: the integration flow has no lifecycle orchestrator, the config-flow walker still acts as the primary entrypoint, the discovery skill does not define a runtime-safe network-scan fallback chain, and the automation drafting path still lacks the vendored Home Assistant best-practices pack.

Overall severity is medium. The main risk is not runtime breakage; it is that the repo now has a stronger first-device path than its surrounding skill architecture, documentation, and automation-authoring guidance actually support.

## Intent

**Goal:** Finish the post-P1 structural cleanup so the first-device experience stays coherent end-to-end, the routing docs tell the truth, and automation drafting picks up the missing Home Assistant best-practices guidance without adding always-on latency.

**Priority ranking:** time-to-first-device-control clarity > accurate operator guidance > keeping the skill/router architecture consistent > minimizing diff size

**Decision boundaries:** The agent may add or reorganize skill documents, update router/docs references, vendor a pinned upstream best-practices snapshot, and add repo-local maintenance scripts. The agent must stop and ask before undoing unrelated user work or recreating a live doc the user intentionally deleted.

**Stop rules:** Stop if an intended P2 touchpoint has already been intentionally removed from the worktree and should stay removed; stop if the upstream best-practices pack cannot be vendored with a clear pinned revision and repo-local provenance; stop if implementing the lifecycle refactor would require changing the approval-gate safety boundary rather than preserving it.

## Findings

### P1: The integration flow lacks a lifecycle-level orchestrator for the post-discovery path

**Severity:** Medium
**Category:** Architecture clarity
**Affected components:** `tools/integrations/`, `TOOLS.md`

**Description:** The repo now has a discovery-first integration flow, but there is no dedicated lifecycle document that defines the full state machine from discovered evidence through verified first control and skill generation. The current structure leaves the transition points and failure handling implicit.

**Impact:** Agents can enter the right discovery flow but still make inconsistent handoffs between discovery, config entry selection, connection, verification, and follow-on skill generation. That weakens the "one first win" setup path that P1 established.

**Success criteria:**
- [ ] `test -f tools/integrations/_lifecycle.md` succeeds.
- [ ] `grep -n "DISCOVERED.*IDENTIFIED.*INTEGRATION_SELECTED.*CONNECTING.*CONNECTED.*VERIFIED.*SKILL_GENERATED" tools/integrations/_lifecycle.md` returns a state-sequence definition.
- [ ] `grep -n "failure" tools/integrations/_lifecycle.md` shows explicit recovery or escalation handling for lifecycle phases.

---

### P2: `tools/integrations/_guide.md` still acts like the primary integration entrypoint instead of a sub-skill

**Severity:** Medium
**Category:** Skill routing
**Affected components:** `tools/integrations/_guide.md`, `TOOLS.md`, routing docs that point agents at the integration flow

**Description:** The current guide mixes entrypoint policy, HACS behavior, dashboard prompting, config-flow walking, and runtime recovery in one place. That made sense before the discovery-first work, but it now leaves the config-flow walker positioned as the main integration interface rather than as a lower-level helper called by a lifecycle skill.

**Impact:** Agents can skip the intended discovery-to-lifecycle handoff, and the repo keeps multiple competing "start here" instructions for the same flow.

**Success criteria:**
- [ ] `grep -n "_lifecycle.md" TOOLS.md tools/integrations/_discovery.md tools/integrations/_guide.md` shows `_lifecycle.md` as the primary route between discovery and guided config work.
- [ ] `grep -n "sub-skill\\|called from" tools/integrations/_guide.md` shows `_guide.md` described as a subordinate config-flow helper rather than the top-level entrypoint.
- [ ] Current-facing routing docs no longer instruct agents to enter the integration flow through `_guide.md` alone.

---

### P3: The discovery skill does not define a capability-aware scan fallback chain before runtime failures happen

**Severity:** Medium
**Category:** Reliability
**Affected components:** `tools/integrations/_discovery.md`

**Description:** `_discovery.md` correctly prefers passive discovery, but it does not yet codify the fallback ladder for active network evidence gathering when privileged or optional tools are unavailable. The checklist explicitly calls for a pre-decided chain: `arp-scan --localnet` → `nmap -sn` → `ip neigh show`.

**Impact:** Agents can waste time trying unsupported commands in an arbitrary order, or mistake a permission/tooling failure for the absence of discoverable devices.

**Success criteria:**
- [ ] `grep -n "arp-scan --localnet" tools/integrations/_discovery.md` returns the first active-scan step.
- [ ] `grep -n "nmap -sn" tools/integrations/_discovery.md` returns the second fallback step.
- [ ] `grep -n "ip neigh show" tools/integrations/_discovery.md` returns the final fallback step.
- [ ] `_discovery.md` distinguishes permission/tool-availability failures from "no candidate devices found" outcomes.

---

### P4: The automation drafting path still lacks the vendored Home Assistant best-practices pack

**Severity:** Medium
**Category:** Authoring guidance
**Affected components:** `tools/automations/_guide.md`, `tools/ha-best-practices/`, `TOOLS.md`, `scripts/`

**Description:** The automation guide currently tells agents to draft automation JSON directly after gathering details and entity IDs. It does not load the best-practices reference pack that the checklist identified as missing, so agents lack the intended anti-pattern guidance, helper-selection matrix, rename caveats, and version-current field conventions during draft creation.

**Impact:** Automation drafts are more likely to repeat avoidable Home Assistant anti-patterns, and the repo misses a reusable guidance layer that should be available offline without adding always-on skill-loading cost.

**Success criteria:**
- [ ] `test -d tools/ha-best-practices` succeeds.
- [ ] `grep -n "home-assistant-best-practices\\|ha-best-practices" tools/automations/_guide.md TOOLS.md` shows the pack wired into the drafting step as advisory guidance.
- [ ] `test -f scripts/update-ha-best-practices.sh` succeeds.
- [ ] The vendored pack records a pinned upstream revision or equivalent provenance so it can be refreshed deliberately.

## Accepted Residual Risks

- The vendored best-practices snapshot will age over time between explicit refreshes; that is acceptable as long as the repo carries a clear pinned revision and a refresh script.
- The lifecycle refactor is intentionally documentation-first. It improves routing consistency, but it does not itself add new Home Assistant runtime capabilities.

## Dependencies Between Findings

- P1 blocks P2 because `_guide.md` cannot be cleanly demoted until `_lifecycle.md` exists as the new orchestrator.
- P2 and P3 both feed the same first-device setup path and should land together so routing and fallback behavior do not drift.
- P4 is independent of P1-P3 at runtime, but it should still respect the same routing/latency principles established elsewhere in the repo.
