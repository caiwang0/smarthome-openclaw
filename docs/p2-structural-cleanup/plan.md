# P2 Structural Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land P2 items 10-12 and 13a so the integration flow routes through a lifecycle skill, discovery has an explicit fallback ladder, and automation drafting can load a vendored Home Assistant best-practices pack offline.

**Architecture:** Treat the integration-flow cleanup as one documentation-and-routing slice: introduce `tools/integrations/_lifecycle.md`, reposition `_guide.md` as the config-flow sub-skill, and update every live router (`CLAUDE.md`, `TOOLS.md`, `README.md`, docs tests) to match. Treat the automation best-practices pack as a separate slice: vendor a pinned upstream snapshot under `tools/ha-best-practices/`, add a refresh script, and wire the pack into the automation drafting step without making it always-on.

**Tech Stack:** Markdown skill files, Bash maintenance script, Python `unittest` doc assertions, `git`/`grep`, GitHub-hosted upstream reference snapshot

---

### Task 1: Introduce the lifecycle entrypoint and reroute the integration flow

**Files:**
- Create: `tools/integrations/_lifecycle.md`
- Modify: `tools/integrations/_guide.md`
- Modify: `tools/integrations/_discovery.md`
- Modify: `TOOLS.md`
- Modify: `CLAUDE.md`
- Modify: `README.md`
- Modify: `tests/test_integrations_docs.py`
- Modify: `docs/p2-structural-cleanup/rdw-state.json`

- [ ] **Step 1: Capture the current routing baseline before edits**

Run:
```bash
grep -RIn "Before adding an integration\\|tools/integrations/_guide.md\\|tools/integrations/_discovery.md" CLAUDE.md TOOLS.md README.md tools tests 2>/dev/null
```

Expected: direct `_guide.md` routing still appears in `CLAUDE.md`, `TOOLS.md`, and `README.md`, while `_discovery.md` already exists as the passive entrypoint.

- [ ] **Step 2: Write the new lifecycle skill**

Create `tools/integrations/_lifecycle.md` with:
- The lifecycle states in one explicit sequence:
  `DISCOVERED → IDENTIFIED → INTEGRATION_SELECTED → CONNECTING → CONNECTED → VERIFIED → SKILL_GENERATED`
- Per-state sections describing:
  - entry conditions
  - required data
  - allowed actions
  - success exit condition
  - failure handling / escalation boundary
- Routing rules that make `_discovery.md` the read-only entrypoint and `_guide.md` the config-flow helper used only during `CONNECTING`
- Verification rules that preserve the P1 “one new device-backed, non-system entity + one verified read or control action” contract before claiming success

- [ ] **Step 3: Demote `_guide.md` to a subordinate config-flow walker**

Edit `tools/integrations/_guide.md` so the opening section:
- calls it a sub-skill / helper
- states that `_discovery.md` and `_lifecycle.md` are the primary path
- keeps the existing config-flow, OAuth, and recovery guidance intact
- points failures back to the lifecycle state handling rather than presenting `_guide.md` as the first stop

- [ ] **Step 4: Update discovery to hand off into lifecycle and define the exact fallback chain**

Edit `tools/integrations/_discovery.md` so the active-scan section is:
1. `arp-scan --localnet`
2. `nmap -sn`
3. `ip neigh show`

Also add explicit decision text for:
- missing command vs insufficient privilege vs empty results
- when to continue down the chain
- when discovery should stop and report “no candidates found”
- handing confirmed candidates into `tools/integrations/_lifecycle.md`

- [ ] **Step 5: Update every live router to the new integration path**

Edit:
- `TOOLS.md`
- `CLAUDE.md`
- `README.md`

So that all integration-routing language follows:
`tools/integrations/_discovery.md` → `tools/integrations/_lifecycle.md` → `tools/integrations/_guide.md`

Also update the README project structure / knowledge-flow sections to mention `_lifecycle.md`.

- [ ] **Step 6: Expand integration docs tests before validating manually**

Update `tests/test_integrations_docs.py` to assert:
- `_lifecycle.md` exists and contains the full state sequence
- `_discovery.md` routes to `_lifecycle.md`
- the active fallback chain order is `arp-scan --localnet` then `nmap -sn` then `ip neigh show`
- `_guide.md` describes itself as a sub-skill/helper
- `CLAUDE.md`, `TOOLS.md`, and `README.md` no longer route integrations directly to `_guide.md`

- [ ] **Step 7: Run the focused integration doc tests**

Run:
```bash
python3 -m unittest tests.test_integrations_docs -v
```

Expected: PASS with the lifecycle/routing assertions green.

### Task 2: Vendor the Home Assistant best-practices pack and wire it into automation drafting

**Files:**
- Create: `tools/ha-best-practices/` (vendored snapshot + provenance file)
- Create: `scripts/update-ha-best-practices.sh`
- Modify: `tools/automations/_guide.md`
- Modify: `TOOLS.md`
- Modify: `README.md`
- Create or Modify: `tests/test_automation_docs.py`
- Modify: `docs/p2-structural-cleanup/rdw-state.json`

- [ ] **Step 1: Inspect the upstream pack and record a pinned revision**

Gather from the upstream `homeassistant-ai/skills` repository:
- the commit SHA being vendored
- the file list for the `home-assistant-best-practices` pack
- enough source context to preserve the pack’s anti-pattern guidance, helper matrix, rename warnings, and version-current gotchas

Expected: a concrete revision is chosen before any repo-local vendoring starts.

- [ ] **Step 2: Vendor the snapshot under `tools/ha-best-practices/`**

Add the upstream content under `tools/ha-best-practices/` and include a short provenance file (for example `README.md`) that records:
- upstream repo URL
- pinned commit SHA
- refresh date
- which upstream directory or files were copied

Expected: the repo contains an offline, committed snapshot rather than an install-time fetch.

- [ ] **Step 3: Add a deterministic refresh script**

Create `scripts/update-ha-best-practices.sh` that:
- accepts no required arguments
- clones or fetches the upstream repo into a temp dir
- checks out the pinned SHA stored in the script or provenance file
- replaces the local vendored snapshot
- prints the SHA it synced

Also make the script fail fast (`set -euo pipefail`) and avoid touching unrelated files.

- [ ] **Step 4: Wire the pack into the automation drafting step only**

Edit `tools/automations/_guide.md` so Step 4 explicitly says to load `tools/ha-best-practices/` when drafting automation JSON, and clarify that:
- the pack is advisory
- `CLAUDE.md` remains authoritative for user-facing behavior
- the pack is loaded only during draft creation, not during every automation interaction

Update `TOOLS.md` so users/agents can find the pack from the automation workflow without making it a universal prerequisite.

- [ ] **Step 5: Add automation doc coverage for the vendored pack**

Create or update `tests/test_automation_docs.py` to assert:
- `tools/ha-best-practices/` exists
- the provenance metadata includes a pinned upstream reference
- `tools/automations/_guide.md` mentions the pack in Step 4 / draft creation
- `TOOLS.md` points automation work to the pack without declaring it authoritative over `CLAUDE.md`
- `scripts/update-ha-best-practices.sh` exists and references the chosen upstream repo / SHA handling

- [ ] **Step 6: Run the focused automation doc tests**

Run:
```bash
python3 -m unittest tests.test_automation_docs -v
```

Expected: PASS with the vendoring/routing assertions green.

### Task 3: Validate the combined P2 slice and update workflow artifacts

**Files:**
- Modify: `docs/fix-checklist.md`
- Create: `docs/p2-structural-cleanup/validation-report.md`
- Modify: `docs/p2-structural-cleanup/rdw-state.json`

- [ ] **Step 1: Mark the checklist scope and completion state accurately**

Update `docs/fix-checklist.md` so:
- item `13` stays removed from P2 scope
- items `10-12` and `13a` reflect the implementation status reached by this work

- [ ] **Step 2: Run the routing/pack verification commands**

Run:
```bash
grep -RIn "Before adding an integration\\|tools/integrations/_guide.md\\|tools/integrations/_lifecycle.md" CLAUDE.md TOOLS.md README.md tools tests 2>/dev/null
grep -RIn "arp-scan --localnet\\|nmap -sn\\|ip neigh show" tools/integrations/_discovery.md tests/test_integrations_docs.py 2>/dev/null
grep -RIn "ha-best-practices\\|home-assistant-best-practices" TOOLS.md tools/automations/_guide.md tools/ha-best-practices scripts/update-ha-best-practices.sh tests/test_automation_docs.py 2>/dev/null
```

Expected: the integration routing points at `_lifecycle.md`, the fallback chain appears in the right order, and the automation best-practices pack is discoverable through the intended files.

- [ ] **Step 3: Run the full focused docs suite for touched surfaces**

Run:
```bash
python3 -m unittest tests.test_integrations_docs tests.test_automation_docs tests.test_setup_docs tests.test_recovery_docs -v
```

Expected: PASS with no regressions in setup or recovery doc contracts.

- [ ] **Step 4: Write the validation report with real evidence**

Create `docs/p2-structural-cleanup/validation-report.md` that records:
- each finding P1-P4
- the grep/unittest commands run
- PASS/FAIL status with actual outputs summarized

- [ ] **Step 5: Mark the workflow complete**

Update `docs/p2-structural-cleanup/rdw-state.json` with:
- `artifacts.validation_report`
- completed stages/phases
- review log entries for plan, implementation phases, and validation

## Self-Review

- Coverage check: Task 1 maps to findings P1-P3, Task 2 maps to P4, and Task 3 validates all four findings plus the item-13 scope removal.
- Placeholder scan: no `TODO`, `TBD`, or undefined upstream-vendoring steps remain.
- Scope check: limited to items `10-12` and `13a`; the removed timing-claim item is intentionally excluded.
