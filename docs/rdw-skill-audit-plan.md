# SmartHub Skill Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Tier 1 Light — execute inline, subagent budget is spent.

**Goal:** Trim ≥100 lines (≥3 KB) of schema-redundant documentation from three SmartHub `tools/` files (findings P1-P3), append a dated correction note to the ha-mcp migration design doc (P4), and verify no SmartHub-specific knowledge or HA quirks were lost in the process.

**Architecture:** Markdown-only cleanup, no code changes. Phases ordered by risk — lowest-risk delete first, highest-risk quirk-preserving rewrite last. Each phase commits independently so any phase is trivially revertible via `git revert <phase-sha>`. Verification is two-pronged: grep for preserved-content strings (prevents silent deletion of quirks) and three live SmartHub smoke tests at Phase 5 (catches behavioral regression).

**Tech Stack:** Markdown files, bash (`wc`, `stat`, `grep`), git. No new dependencies, no new test frameworks, no TDD — there is no code to test. "Test" here means (1) grep verification of preserved-content strings and (2) live SmartHub smoke tests against a real HA instance.

**Constraints from Intent** (`docs/rdw-skill-audit.md` §Intent):
- **Correctness > latency > minimalism.** When in doubt, keep.
- **Abort condition:** if Phase 5 measures <50 lines cut total, STOP and recommend defer (option 3 from the original audit framing).
- **Stop rule:** if any section flagged for deletion turns out to contain quirks during implementation, reclassify as keep and re-scope the phase.

**Reference documents:**
- Issue doc: `docs/rdw-skill-audit.md` (225 lines, all 4 findings + Intent + Workflow Completion Criteria + Keep List)
- State file: `docs/rdw-state-skill-audit.json`
- RDW tier: Tier 1 Light (0-2 subagent budget, both already spent in Stage 1)

---

## File Structure

**Files modified (content changes):**
- `tools/_ha-mcp.md` → **deleted entirely** (currently 45 lines, 100% redundant + contains stale tool name `ha_config_delete_automation`)
- `tools/_common.md` → lines 10-49 removed, 14 lines remain (currently 54 lines)
- `tools/_services.md` → rewritten to ≤30 lines (currently 85 lines), preserving 8 quirk strings + brightness conversion
- `TOOLS.md` → one row (line 12) removed from the Quick Reference table
- `docs/superpowers/specs/2026-04-09-ha-mcp-integration-design.md` → dated correction note **appended at end** (currently 642 lines; original lines 496-504 preserved)

**Files updated (workflow state):**
- `docs/rdw-state-skill-audit.json` → baseline captured as D2 in Phase 0, phases logged after each commit, final validation report inlined in Phase 5

**Files explicitly NOT touched** (on the Keep List per issue doc §"Files NOT Flagged for Any Change"):
- `tools/_errors.md` (historical meta-note on line 27 is a regression anchor)
- `tools/automations/**`, `tools/integrations/**`, `tools/xiaomi-home/**`, `tools/printer/**`, `tools/setup.md`
- `CLAUDE.md`, `docs/rdw-skill-audit.md` (source of truth)
- `docs/rdw-state.json` (a different workflow's state file — ha-mcp-migration phase-6)

---

## Phase 0: Baseline Capture

**Goal:** Record pre-cut line counts and byte sizes so Phase 5 can compute the delta. Without this, we can't prove the ≥100-line / ≥3 KB gates.

**Risk:** None (read-only measurement + JSON edit).

### Task 0.1: Capture pre-cut metrics

**Files:**
- Read-only: `tools/_ha-mcp.md`, `tools/_common.md`, `tools/_services.md`

- [ ] **Step 1: Run wc -l on the three files P1/P2/P3 will touch**

```bash
wc -l tools/_ha-mcp.md tools/_common.md tools/_services.md
```

Expected output (will become the D2 baseline in Task 0.2):
```
  45 tools/_ha-mcp.md
  54 tools/_common.md
  85 tools/_services.md
 184 total
```

If any count differs from the above, **STOP** — the repo has drifted from the issue doc's analysis. Re-verify the issue doc against current reality before continuing.

- [ ] **Step 2: Run stat on the same three files for byte sizes**

```bash
stat -c '%s %n' tools/_ha-mcp.md tools/_common.md tools/_services.md
```

Record the three byte values. Sum them — this is the baseline byte total for the Phase 5 ≥3 KB gate.

### Task 0.2: Append D2 discovery to state file

**Files:**
- Modify: `docs/rdw-state-skill-audit.json`

- [ ] **Step 1: Add D2 entry to the `discoveries` array**

Use the Edit tool to append a second entry to the `discoveries` array in `docs/rdw-state-skill-audit.json`, right after the D1 object. Shape:

````json
{
  "id": "D2",
  "stage": "implement",
  "phase": "phase-0-baseline",
  "date": "2026-04-10",
  "summary": "Pre-cut baseline metrics for the three files P1/P2/P3 will touch",
  "wc_l": {
    "tools/_ha-mcp.md": 45,
    "tools/_common.md": 54,
    "tools/_services.md": 85,
    "total": 184
  },
  "stat_bytes": {
    "tools/_ha-mcp.md": <FROM TASK 0.1 STEP 2>,
    "tools/_common.md": <FROM TASK 0.1 STEP 2>,
    "tools/_services.md": <FROM TASK 0.1 STEP 2>,
    "total": <SUM>
  },
  "purpose": "Delta gate for Phase 5 validation: ≥100 lines cut, ≥3 KB bytes cut"
}
````

Replace the four `<...>` markers with the actual integers from Task 0.1 Step 2.

- [ ] **Step 2: Update top-level state fields**

In the same Edit call or a second one, also update:
- `current_stage`: `"implement_phase_0_baseline_captured"`
- `phases.total`: `6`
- `phases.current`: `"phase-0-baseline"`

### Task 0.3: Commit baseline

- [ ] **Step 1: Commit the state-file update**

```bash
git add docs/rdw-state-skill-audit.json
git commit -m "chore(rdw): capture baseline metrics for skill audit Phase 0"
```

---

## Phase 1: P1 — Delete `tools/_ha-mcp.md`

**Goal:** Remove the 45-line tool-schema-duplicating file and its one cross-reference in `TOOLS.md`.

**Risk:** Lowest of all phases. The file contains zero SmartHub-specific knowledge AND has one actively-wrong tool name (`ha_config_delete_automation` vs real `ha_config_remove_automation`) — deleting it also fixes a latent bug.

### Task 1.1: Pre-delete cross-reference scan

- [ ] **Step 1: Grep the repo for references to `_ha-mcp.md`**

```bash
grep -rn "_ha-mcp\.md" --include="*.md" --include="*.json" --include="*.sh" --include="*.py" .
```

Expected: at most two matches:
- `TOOLS.md:12` — the Quick Reference row
- `tools/_ha-mcp.md` itself may match if grep's output includes the filename path

**If a match appears in `CLAUDE.md`, `tools/setup.md`, `install.sh`, or any Keep List file, STOP** and re-scope — the file is referenced outside `TOOLS.md` and deletion requires additional edits that weren't scoped in the issue doc.

### Task 1.2: Delete `tools/_ha-mcp.md`

- [ ] **Step 1: Remove the file (staged delete)**

```bash
git rm tools/_ha-mcp.md
```

Use `git rm` not plain `rm` so the deletion is already staged.

### Task 1.3: Remove the `TOOLS.md` row

**Files:**
- Modify: `TOOLS.md:12`

- [ ] **Step 1: Use the Edit tool to remove the `_ha-mcp.md` row from the Quick Reference table**

`old_string`:
```
| [tools/_services.md](tools/_services.md) | Per-domain service reference (light, climate, media_player, etc.) |
| [tools/_ha-mcp.md](tools/_ha-mcp.md) | ha-mcp tool quick reference — device control, automations, integrations, helpers |
| [tools/integrations/_guide.md](tools/integrations/_guide.md) | Integration setup — HACS, config flows, OAuth, error handling |
```

`new_string`:
```
| [tools/_services.md](tools/_services.md) | Per-domain service reference (light, climate, media_player, etc.) |
| [tools/integrations/_guide.md](tools/integrations/_guide.md) | Integration setup — HACS, config flows, OAuth, error handling |
```

This is a three-line-to-two-line replacement; the `_ha-mcp.md` row is dropped, the surrounding two rows are the unique-context anchors.

### Task 1.4: Post-delete verification

- [ ] **Step 1: Re-run the cross-reference grep**

```bash
grep -rn "_ha-mcp\.md" --include="*.md" --include="*.json" --include="*.sh" --include="*.py" .
```

Expected: **zero matches**. If any match remains, STOP and resolve it before committing.

- [ ] **Step 2: Verify `TOOLS.md` Quick Reference row count dropped by exactly 1**

```bash
grep -c "^| \[tools/" TOOLS.md
```

Expected: `10` (was `11` before the delete).

### Task 1.5: Commit Phase 1

- [ ] **Step 1: Commit file delete + `TOOLS.md` update together**

```bash
git add TOOLS.md tools/_ha-mcp.md
git commit -m "$(cat <<'EOF'
docs: Phase 1 — delete tools/_ha-mcp.md (P1 of skill audit)

The file duplicated ha-mcp tool schemas 1:1 and contained a stale
tool name (ha_config_delete_automation; real: ha_config_remove_automation).
Removing it frees 45 lines of LLM context per conversation and
eliminates a latent tool-call bug. TOOLS.md Quick Reference updated
to drop the row. See docs/rdw-skill-audit.md P1.
EOF
)"
```

### Task 1.6: Update state file

- [ ] **Step 1: Append phase-1 to `phases.completed`, advance `phases.current`**

Edit `docs/rdw-state-skill-audit.json`:
- Append `"phase-1-delete-ha-mcp-md"` to `phases.completed`
- Set `phases.current` to `"phase-2-trim-common-md"`
- Set `current_stage` to `"implement_phase_1_complete"`
- Append a new entry to `review_log`:
  ```json
  {"stage": "implement-phase-1", "round": 1, "result": "PASS", "note": "File deleted, TOOLS.md row removed, zero remaining references (grep clean)"}
  ```

- [ ] **Step 2: Commit the state update**

```bash
git add docs/rdw-state-skill-audit.json
git commit -m "chore(rdw): mark phase-1 complete in skill audit state"
```

---

## Phase 2: P2 — Trim `tools/_common.md`

**Goal:** Remove lines 10-49 of `_common.md` (the "## Commonly Used Tools" section, 40 lines of schema-duplicating fenced blocks), preserve lines 1-9 (header + migration context + auth note) and lines 50-54 (network info).

**Risk:** Low. The delete range is a contiguous block with well-defined start (`## Commonly Used Tools`) and end (blank line before `## Network Info`). Preserved content is non-overlapping and anchored by distinctive strings.

**Post-edit target:** 14 lines.

### Task 2.1: Pre-edit preserved-content grep baseline

- [ ] **Step 1: Confirm the three "must survive" strings are currently present**

```bash
grep -F "No curl. No API routing." tools/_common.md
grep -F "HOMEASSISTANT_TOKEN" tools/_common.md
grep -F "homeassistant.local" tools/_common.md
```

Expected: three matches (one per command). If any returns empty, STOP — the file has already drifted from the issue doc.

### Task 2.2: Edit `_common.md`

**Files:**
- Modify: `tools/_common.md` (remove lines 10-49)

- [ ] **Step 1: Use the Edit tool to delete the "Commonly Used Tools" section**

The old_string contains nested triple-backtick fences, so the plan shows it as an indented block. Use this literal text as `old_string` (all 40 lines from `## Commonly Used Tools` through the blank line before `## Network Info`):

    ## Commonly Used Tools

    ### Search entities
    ```
    Tool: ha_search_entities
      query: "<search term>"
    ```

    ### Get entity state
    ```
    Tool: ha_get_state
      entity_id: "<entity_id>"
    ```

    ### Call a service (device control)
    ```
    Tool: ha_call_service
      domain: "<domain>"
      service: "<service>"
      entity_id: "<entity_id>"
      data: { ... }
    ```

    ### List areas
    ```
    Tool: ha_get_areas
    ```

    ### Config entries
    ```
    Tool: ha_config_entries_get
    ```

    ### Find the right tool
    When unsure which tool to use:
    ```
    Tool: ha_search_tools
      query: "<what you want to do>"
    ```

    ## Network Info

`new_string` (just the surviving heading, which stays as the anchor):

    ## Network Info

Both strings share `## Network Info` so the Edit call replaces 40 lines with 1 line (net −39 lines). After the edit, the file should be 14 lines — lines 1-9 of the original, the now-promoted `## Network Info` heading, and the 3 network info lines + final newline.

**Expected post-edit file contents** (exact, for verification):

```markdown
# Common — ha-mcp Tool Reference

## How Device Control Works

All HA interaction goes through ha-mcp tools (MCP protocol, stdio).
No curl. No API routing. No ports to configure.

ha-mcp handles authentication internally via HOMEASSISTANT_TOKEN env var.

## Network Info

- Home Assistant: `http://homeassistant.local:<HA_PORT>` (read `HA_PORT` from `.env`; default 8123)
- ha-mcp: stdio process (no port, no URL) — spawned by Claude Code or OpenClaw
- mDNS: `homeassistant.local` resolves to the Pi's IP on the LAN
```

### Task 2.3: Post-edit verification

- [ ] **Step 1: Re-run the preserved-content grep (must still pass)**

```bash
grep -F "No curl. No API routing." tools/_common.md
grep -F "HOMEASSISTANT_TOKEN" tools/_common.md
grep -F "homeassistant.local" tools/_common.md
grep -F "Network Info" tools/_common.md
```

Expected: four matches, one per command.

- [ ] **Step 2: Verify the "Commonly Used Tools" section is gone**

```bash
grep -F "Commonly Used Tools" tools/_common.md
grep -F "ha_search_entities" tools/_common.md
```

Expected: **zero matches** for both.

- [ ] **Step 3: Verify final line count**

```bash
wc -l tools/_common.md
```

Expected: `14` (± 1 for trailing-newline variance). If >20, something wasn't removed. If <10, too much was removed — restore from git and retry.

### Task 2.4: Commit Phase 2

- [ ] **Step 1: Commit the trim**

```bash
git add tools/_common.md
git commit -m "$(cat <<'EOF'
docs: Phase 2 — trim tools/_common.md (P2 of skill audit)

Removes the "Commonly Used Tools" section (lines 10-49) which
duplicated ha-mcp tool schemas 1:1. Preserves the migration context
("No curl. No API routing."), auth note, and network info — all
SmartHub-specific content not available from tool schemas alone.
40 lines cut. See docs/rdw-skill-audit.md P2.
EOF
)"
```

### Task 2.5: Update state file

- [ ] **Step 1: Append phase-2 to state**

Edit `docs/rdw-state-skill-audit.json`:
- Append `"phase-2-trim-common-md"` to `phases.completed`
- Set `phases.current` to `"phase-3-rewrite-services-md"`
- Set `current_stage` to `"implement_phase_2_complete"`
- Append review_log entry:
  ```json
  {"stage": "implement-phase-2", "round": 1, "result": "PASS", "note": "Lines 10-49 removed, 4 preserved strings grep-verified (No curl, HOMEASSISTANT_TOKEN, homeassistant.local, Network Info), final line count 14"}
  ```

- [ ] **Step 2: Commit**

```bash
git add docs/rdw-state-skill-audit.json
git commit -m "chore(rdw): mark phase-2 complete in skill audit state"
```

---

## Phase 3: P3 — Restructure `tools/_services.md`

**Goal:** Rewrite the 85-line `_services.md` to a ≤30-line replacement that preserves the full Quirks Inventory (8 strings) and the Brightness Conversion section verbatim, while dropping the schema-duplicating per-domain service tables.

**Risk:** Highest of all phases. This is a full rewrite, not a delete. The service tables embed critical quirks in their "Notes" columns — a naive delete would silently lose SmartHub-specific HA knowledge. Mitigation: pre-verify the 8 quirk strings against the current file (Task 3.1), write the replacement (Task 3.2), re-verify all 8 strings survive (Task 3.3). If any grep fails post-rewrite, restore from git and retry.

### Task 3.1: Pre-rewrite quirks grep baseline (ground truth)

- [ ] **Step 1: Confirm all 8 quirks inventory strings are present in the current file**

```bash
grep -F "States ARE HVAC modes" tools/_services.md
grep -F "May not work if device disconnects Wi-Fi in standby" tools/_services.md
grep -F "Check entity attributes for available sources" tools/_services.md
grep -F "Check entity attributes for available options" tools/_services.md
grep -F "Check entity attributes for min/max/step" tools/_services.md
grep -F "Brightness in HA is 0-255, not 0-100%" tools/_services.md
grep -F "brightness = percentage × 2.55" tools/_services.md
grep -E "25%\s*\|\s*64" tools/_services.md
```

Expected: **8 matches**, one per command. If any returns empty, the file has drifted from the issue doc's analysis — STOP and re-verify the issue doc's Quirks Inventory against the current file before proceeding.

### Task 3.2: Write the replacement file

**Files:**
- Rewrite: `tools/_services.md` (full file replacement via Write tool)

- [ ] **Step 1: Read the file first (required by Write tool contract for existing files)**

```
Read tools/_services.md
```

(Even though we're replacing it wholesale, the Write tool requires a prior Read for existing files.)

- [ ] **Step 2: Use the Write tool to replace the entire file contents**

Write this exact content to `tools/_services.md`:

```markdown
# Services by Domain — Quirks & Patterns

> For the full per-domain service catalog, call `ha_list_services` (e.g., `ha_list_services(domain="light")`). This file keeps only the SmartHub-specific quirks and conversion rules the LLM cannot derive from tool schemas.

## Quirks & Patterns

- **`climate.set_hvac_mode`** — States ARE HVAC modes, not on/off. The `state` of a `climate.*` entity is the current HVAC mode string (`off`, `cool`, `heat`, `heat_cool`, `auto`, `dry`, `fan_only`), not a boolean. Don't compare entity state to `"on"` or `"off"`.
- **`media_player.turn_on`** — May not work if device disconnects Wi-Fi in standby. If `turn_on` silently fails, the device is likely off-network; tell the user and suggest a physical power check instead of retrying.
- **`media_player.select_source`** — Check entity attributes for available sources. Read the `source_list` attribute from `ha_get_state` before calling — sources are per-device.
- **`select.select_option`** — Check entity attributes for available options. Read the `options` attribute from `ha_get_state` before calling.
- **`number.set_value`** — Check entity attributes for min/max/step. Read `min`, `max`, `step` attributes from `ha_get_state` before calling; setting a value outside the range can fail silently on some integrations.

## Brightness Conversion

Brightness in HA is 0-255, not 0-100%. To convert from percentage: `brightness = percentage × 2.55`

| User says | brightness value |
|-----------|-----------------|
| 25% | 64 |
| 50% | 128 |
| 75% | 191 |
| 100% | 255 |
```

The replacement is 23 lines including the trailing newline (well under the 30-line target). Every string from the Quirks Inventory appears verbatim.

### Task 3.3: Post-rewrite quirks grep verification

- [ ] **Step 1: Re-run the 8 grep commands from Task 3.1**

```bash
grep -F "States ARE HVAC modes" tools/_services.md
grep -F "May not work if device disconnects Wi-Fi in standby" tools/_services.md
grep -F "Check entity attributes for available sources" tools/_services.md
grep -F "Check entity attributes for available options" tools/_services.md
grep -F "Check entity attributes for min/max/step" tools/_services.md
grep -F "Brightness in HA is 0-255, not 0-100%" tools/_services.md
grep -F "brightness = percentage × 2.55" tools/_services.md
grep -E "25%\s*\|\s*64" tools/_services.md
```

Expected: **8 matches**, identical to Task 3.1. If **any** command returns empty, STOP — the rewrite lost a quirk. Restore the file from git (`git checkout tools/_services.md`) and redo the Write step, this time double-checking the missing quirk is included.

- [ ] **Step 2: Verify brightness conversion lookup table is complete**

```bash
grep -c "^| [0-9]" tools/_services.md
```

Expected: `4` (one row per percentage: 25%, 50%, 75%, 100%).

- [ ] **Step 3: Verify final line count is within target**

```bash
wc -l tools/_services.md
```

Expected: ≤30 lines (target ~23). If >30, re-review — either compress further or note the overage in the commit message.

### Task 3.4: Commit Phase 3

- [ ] **Step 1: Commit the rewrite**

```bash
git add tools/_services.md
git commit -m "$(cat <<'EOF'
docs: Phase 3 — restructure tools/_services.md (P3 of skill audit)

Shrinks _services.md from 85 lines to ~23 lines by removing the
per-domain service tables (redundant with ha_list_services) while
preserving all 8 HA-specific quirks (climate HVAC mode as state,
media_player Wi-Fi standby, source/option/min-max attribute lookups)
and the full brightness conversion section. Quirks inventory
grep-verified both pre- and post-rewrite (8/8 strings present).
See docs/rdw-skill-audit.md P3.
EOF
)"
```

### Task 3.5: Update state file

- [ ] **Step 1: Append phase-3 to state**

Edit `docs/rdw-state-skill-audit.json`:
- Append `"phase-3-rewrite-services-md"` to `phases.completed`
- Set `phases.current` to `"phase-4-correction-note"`
- Set `current_stage` to `"implement_phase_3_complete"`
- Append review_log entry:
  ```json
  {"stage": "implement-phase-3", "round": 1, "result": "PASS", "note": "File rewritten to ~23 lines, 8/8 quirks inventory strings verified via grep both pre- and post-rewrite, 4/4 brightness table rows preserved"}
  ```

- [ ] **Step 2: Commit**

```bash
git add docs/rdw-state-skill-audit.json
git commit -m "chore(rdw): mark phase-3 complete in skill audit state"
```

---

## Phase 4: P4 — Append correction note to ha-mcp migration design doc

**Goal:** Append a dated correction note at the end of `docs/superpowers/specs/2026-04-09-ha-mcp-integration-design.md` explaining that ha-mcp 7.2.0 PyPI wheel ships no bundled skills — **without** editing the original lines 496-504 (which are historical record).

**Risk:** Low. Append-only edit, cannot damage existing content if done correctly. Verification is a simple grep for the original passage plus the new note.

### Task 4.1: Verify current file length and original passage integrity

- [ ] **Step 1: Confirm the design doc is still 642 lines**

```bash
wc -l docs/superpowers/specs/2026-04-09-ha-mcp-integration-design.md
```

Expected: `642`. If larger, someone edited the doc since Stage 1 — re-read lines 496-504 before proceeding to confirm the original passage is still there.

- [ ] **Step 2: Confirm the original passage text at line 504 is intact**

```bash
grep -n "Keep both. No conflict. No deduplication needed." docs/superpowers/specs/2026-04-09-ha-mcp-integration-design.md
```

Expected: **exactly one match at line 504**. This is the landmark string we protect.

### Task 4.2: Capture the tail of the file as an Edit anchor

- [ ] **Step 1: Read the last 5 lines of the file so the Edit `old_string` has a unique anchor**

```bash
tail -5 docs/superpowers/specs/2026-04-09-ha-mcp-integration-design.md
```

Record the exact last few lines — whatever they are, they become the unique `old_string` anchor for the append-edit. (The plan cannot hardcode them because they depend on the file's current content; the engineer captures them at runtime.)

### Task 4.3: Append the correction note

**Files:**
- Modify: `docs/superpowers/specs/2026-04-09-ha-mcp-integration-design.md` (append-only)

- [ ] **Step 1: Use the Edit tool to append after the last line**

`old_string`: the exact last line(s) captured in Task 4.2 (use at least the last 3 lines so the anchor is unique within the doc).

`new_string`: the same exact last line(s) from `old_string`, followed by two blank lines, followed by this correction note:

```markdown

---

## 2026-04-10 Correction — ha-mcp 7.2.0 Bundled Skills Claim

**Added by:** `rdw-20260410-skill-audit` workflow
**Affects:** Primarily lines 496-504 ("ha-mcp skills vs our skill files"); secondary context at lines 58, 120-121, and 472.
**Original content preserved above** — this is an append-only correction, not an in-place edit.

The "ha-mcp skills vs our skill files" section above (lines 496-504) asserts that ha-mcp bundles general HA best-practice skills (automation patterns, helper selection, etc.). A verification pass on 2026-04-10 discovered this is **false for the PyPI wheel** that SmartHub installs via `uvx ha-mcp@7.2.0`.

**Evidence** (see `docs/rdw-state-skill-audit.json` Discovery D1 for full details):
- The wheel `RECORD` at `~/.cache/uv/archive-v0/*/lib/python3.13/site-packages/ha_mcp-7.2.0.dist-info/RECORD` contains zero `.md` files and no `resources/` directory entries.
- `ha_mcp/server.py:146` `_get_skills_dir()` returns `None` because `resources/skills-vendor/skills/` does not exist in the installed package.
- `ha_mcp/server.py:471` `_register_skills()` logs a warning and exits early when `skills_dir is None`.
- `ListMcpResourcesTool` for the `ha-mcp` server returns "No resources found" at runtime.
- The `ENABLE_SKILLS=true` and `ENABLE_SKILLS_AS_TOOLS=true` env vars in `.claude/settings.json` silently have no effect — there are no skills to load.

**Root cause:** The `resources/skills-vendor/` directory is a git submodule in the ha-mcp source repository and gets stripped from the PyPI wheel build. The code paths exist but never fire for wheel-installed users.

**Impact on the migration design:** The statement "ha-mcp bundles general HA best-practice skills" and the "Keep both. No conflict. No deduplication needed." conclusion remain **operationally correct** — we still keep both sets of files — but the *reason* cited was wrong. SmartHub's `tools/*.md` files are complementary to **raw ha-mcp tool schemas**, not to bundled ha-mcp skills, because there are no bundled ha-mcp skills. This changes how future contributors should think about deduplication: the reference point is the MCP tool schema layer, not a parallel skill layer.

**Follow-up:** Potential upstream packaging bug in ha-mcp deferred (not filed with homeassistant-ai/ha-mcp). Re-evaluate if a future ha-mcp release ships the `resources/skills-vendor/` submodule in the wheel.
```

### Task 4.4: Post-append verification

- [ ] **Step 1: Verify the original passage still exists unchanged**

```bash
grep -n "Keep both. No conflict. No deduplication needed." docs/superpowers/specs/2026-04-09-ha-mcp-integration-design.md
```

Expected: **exactly one match, still at line 504**. The correction note must NOT have overwritten or moved the original.

- [ ] **Step 2: Verify the correction note was added**

```bash
grep -n "2026-04-10 Correction" docs/superpowers/specs/2026-04-09-ha-mcp-integration-design.md
```

Expected: **exactly one match**, with line number > 642.

- [ ] **Step 3: Verify key evidence strings appear in the note**

```bash
grep -F "Discovery D1" docs/superpowers/specs/2026-04-09-ha-mcp-integration-design.md
grep -F "resources/skills-vendor" docs/superpowers/specs/2026-04-09-ha-mcp-integration-design.md
grep -F "_register_skills" docs/superpowers/specs/2026-04-09-ha-mcp-integration-design.md
```

Expected: one match per command (in the new correction note section).

- [ ] **Step 4: Confirm new total line count**

```bash
wc -l docs/superpowers/specs/2026-04-09-ha-mcp-integration-design.md
```

Expected: between 670 and 685 lines (642 baseline + ~25-35 lines of correction note).

### Task 4.5: Commit Phase 4

- [ ] **Step 1: Commit the correction note**

```bash
git add docs/superpowers/specs/2026-04-09-ha-mcp-integration-design.md
git commit -m "$(cat <<'EOF'
docs: Phase 4 — append D1 correction to ha-mcp migration design

Appends a 2026-04-10 correction note clarifying that ha-mcp 7.2.0
PyPI wheel ships no bundled skills — the resources/skills-vendor/
submodule is stripped at wheel build time. Original lines 496-504
preserved as historical record (append-only, no in-place edit).
See docs/rdw-skill-audit.md P4 and docs/rdw-state-skill-audit.json
Discovery D1.
EOF
)"
```

### Task 4.6: Update state file

- [ ] **Step 1: Append phase-4 to state**

Edit `docs/rdw-state-skill-audit.json`:
- Append `"phase-4-correction-note"` to `phases.completed`
- Set `phases.current` to `"phase-5-validation"`
- Set `current_stage` to `"implement_phase_4_complete"`
- Append review_log entry:
  ```json
  {"stage": "implement-phase-4", "round": 1, "result": "PASS", "note": "Correction note appended after line 642, original lines 496-504 preserved (grep-verified), Discovery D1 evidence included in note"}
  ```

- [ ] **Step 2: Commit**

```bash
git add docs/rdw-state-skill-audit.json
git commit -m "chore(rdw): mark phase-4 complete in skill audit state"
```

---

## Phase 5: Validation — Workflow Completion Gates

**Goal:** Verify all gates from `docs/rdw-skill-audit.md` §"Workflow Completion Criteria" pass, decide go/no-go, and advance the workflow to `validate_complete`.

**Risk:** None on the compute-delta steps (read-only). Smoke tests are user-run and can reveal latent regressions, but failures here mean rollback, not corruption.

### Task 5.1: Compute line delta

- [ ] **Step 1: Measure post-cut line counts**

```bash
wc -l tools/_common.md tools/_services.md 2>/dev/null
test -e tools/_ha-mcp.md && echo "ERROR: _ha-mcp.md still exists" || echo "OK: _ha-mcp.md deleted"
```

Expected:
- `tools/_common.md`: 14 lines
- `tools/_services.md`: ≤30 lines (likely ~23)
- `tools/_ha-mcp.md`: prints `OK: _ha-mcp.md deleted`

- [ ] **Step 2: Compute delta against D2 baseline**

Baseline (from D2 in state file): `45 + 54 + 85 = 184` lines.
Post-cut: `0 + 14 + ~23 = ~37` lines.
**Delta: ≈ 147 lines removed.**

**Gate check:** must be **≥100 lines**. If <100, something was under-cut — investigate each phase's delta before advancing. (Expected delta ~147, well above the floor.)

### Task 5.2: Compute byte delta

- [ ] **Step 1: Measure post-cut byte sizes**

```bash
stat -c '%s %n' tools/_common.md tools/_services.md
```

- [ ] **Step 2: Compute byte delta against D2 baseline**

`delta_bytes = D2.stat_bytes.total − (0 + current_common_md_bytes + current_services_md_bytes)`

**Gate check:** must be **≥3072 bytes** (3 KB). If <3 KB, investigate.

### Task 5.3: Abort-condition check (issue doc stop rule)

- [ ] **Step 1: If the line delta from Task 5.1 is < 50, STOP the workflow**

This should not trigger (expected delta ~147, well above the 50-line floor), but the check exists per the Intent's stop rule. If it triggers:
1. Do NOT proceed to smoke tests.
2. Update `docs/rdw-state-skill-audit.json`:
   - `current_stage`: `"aborted_under_floor"`
   - Add top-level key `"aborted": {"reason": "line delta <50", "actual": <N>, "decision_required": "revert or keep partial cut"}`
3. Ask the user whether to `git revert` all phase commits or keep the partial cut.

### Task 5.4: Live smoke tests

**These are manual tests the agent cannot run itself — they require the user to invoke OpenClaw against a live Home Assistant instance.**

- [ ] **Step 1: Present the three smoke prompts to the user and wait for results**

Print this block verbatim to the user:

> **Phase 5 smoke tests — please run these three prompts in a live SmartHub session and report back:**
>
> 1. **"turn on the TV"** — confirms tool discovery still works after `_ha-mcp.md` deletion and `_common.md` trim. Expected: TV turns on (or a clear "device offline" message if it's in Wi-Fi standby — that's also a pass for the media_player quirk).
> 2. **"dim lights to 50%"** — confirms the brightness conversion quirk survived the `_services.md` rewrite. Expected: light at brightness value 128 (50% × 2.55).
> 3. **"set AC to 24 degrees"** — confirms the HVAC mode quirk survived. Expected: climate set to cool mode at 24°C without a state-comparison error.
>
> For each: reply PASS or FAIL + any error message.

- [ ] **Step 2: Record the results**

If **all three pass** → proceed to Task 5.5.
If **any fail** → STOP, investigate which quirk was lost, consider `git revert` of the relevant phase, re-plan.

### Task 5.5: Final state file update

- [ ] **Step 1: Mark Phase 5 complete and advance workflow stage**

Edit `docs/rdw-state-skill-audit.json`:
- Append `"phase-5-validation"` to `phases.completed`
- Set `phases.current` to `null`
- Set `current_stage` to `"validate_complete"`
- Set `artifacts.validation_report` to `"inline in review_log phase-5 entry"` (Tier 1 — no separate report doc)
- Append review_log entry:
  ```json
  {
    "stage": "validate",
    "round": 1,
    "result": "PASS",
    "line_delta": <N from Task 5.1>,
    "byte_delta": <N from Task 5.2>,
    "smoke_tests": {
      "turn_on_tv": "PASS",
      "dim_lights_50": "PASS",
      "set_ac_24": "PASS"
    },
    "note": "All gates pass: ≥100 lines (actual <N>), ≥3 KB (actual <N>), 3/3 smoke tests"
  }
  ```

- [ ] **Step 2: Commit final state**

```bash
git add docs/rdw-state-skill-audit.json
git commit -m "$(cat <<'EOF'
chore(rdw): Phase 5 validation complete — skill audit passes all gates

Line delta: <N> ≥ 100. Byte delta: <N> ≥ 3 KB. Three live smoke tests
pass (turn_on_tv, dim_lights_50, set_ac_24). Workflow advances to
Stage 5 (memory capture).
EOF
)"
```

### Task 5.6: Stage 5 memory capture handoff

- [ ] **Step 1: Invoke the `memory-capture` skill**

Per RDW Stage 5 rules, scan `docs/rdw-state-skill-audit.json` for discoveries, review failures, and validation fixes. Candidate learnings:
- **Discovery D1** (ha-mcp 7.2.0 wheel ships no bundled skills — likely a ha-mcp packaging bug) → candidate for a **reference** or **project** memory so a future Claude doesn't re-investigate the same question.
- **Quirk-preservation pattern** (pre-enumerated grep inventory as compound test for lossy rewrites) → candidate for a **feedback** memory if the user confirms this approach worked.

Skip memory capture if the workflow yielded nothing non-obvious worth remembering across sessions.

- [ ] **Step 2: Set workflow to complete**

Edit `docs/rdw-state-skill-audit.json`:
- Set `current_stage` to `"complete"`
- Add `completed_at` ISO-8601 timestamp

```bash
git add docs/rdw-state-skill-audit.json
git commit -m "chore(rdw): skill audit workflow complete"
```

---

## Self-Review Checklist

**Spec coverage** — every finding in `docs/rdw-skill-audit.md` maps to at least one phase:

| Issue doc item | Plan coverage |
|---|---|
| P1 (delete `_ha-mcp.md`) | Phase 1 (Tasks 1.1-1.6) |
| P2 (trim `_common.md`) | Phase 2 (Tasks 2.1-2.5) |
| P3 (restructure `_services.md`, preserve 8 quirks) | Phase 3 (Tasks 3.1-3.5), grep verification pre+post |
| P4 (design doc correction note) | Phase 4 (Tasks 4.1-4.6), append-only |
| Workflow Completion Criteria → baseline capture | Phase 0 (Tasks 0.1-0.3) |
| Workflow Completion Criteria → ≥100-line gate | Task 5.1 |
| Workflow Completion Criteria → ≥3 KB gate | Task 5.2 |
| Workflow Completion Criteria → 3 smoke tests | Task 5.4 |
| Intent abort condition (<50 lines) | Task 5.3 |
| Intent stop rule (lose a quirk → reclassify) | Task 3.3 (post-rewrite grep) |
| Keep List (don't touch other files) | File Structure section, explicit non-goals |

**Placeholder scan:** Every file path is exact. Every grep / wc / stat command is copy-pasteable. The only runtime-computed values are byte counts in Task 0.3 (templated as `<FROM TASK 0.1 STEP 2>`) and delta values in Task 5.5 (templated as `<N>`) — these are instructions to fill in measurements, not undefined placeholders.

**Type consistency:** N/A (markdown-only plan).

**Dependencies between phases:** Per the issue doc's Dependencies section, P1/P2/P3/P4 are all independent. The plan orders them by risk (lowest first) so rollback is cheap if any phase fails:
- Phase 1 (delete) is the most reversible via `git revert`.
- Phase 2 (trim with well-defined anchors) is next.
- Phase 3 (rewrite) is highest-risk and has the most verification.
- Phase 4 (append-only doc edit) is independent of P1-P3 and could technically go anywhere.

**Commit granularity:** Each phase commits separately (content commit + state commit) so any phase can be reverted in isolation without touching the others.

---

## Execution Handoff

**Plan complete and saved to `docs/rdw-skill-audit-plan.md`.**

Tier 1 Light. Subagent budget is spent (0/2 remaining). Stage 3 execution options:

1. **Inline Execution (recommended)** — Execute the plan task-by-task in the current session using `superpowers:executing-plans`. Pause after each phase commit for user review. This is the correct choice for Tier 1.
2. **Subagent-Driven** — NOT RECOMMENDED. The Tier 1 budget is already spent and per-phase subagent dispatch would blow through it.

**Waiting for user approval before starting Phase 0.**
