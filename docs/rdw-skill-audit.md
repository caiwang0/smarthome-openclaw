# SmartHub tools/ Redundancy Audit — Issue Document

**Date:** 2026-04-10
**Scope:** SmartHub `tools/*.md` files — determine which are genuinely redundant with ha-mcp tool schemas after the ha-mcp migration
**Analyst:** Claude (main thread) + Explore subagent for cross-reference analysis
**RDW workflow:** `rdw-20260410-skill-audit` (Tier 1 Light)
**State file:** `docs/rdw-state-skill-audit.json`

## Summary

After the ha-mcp migration completed (workflow `rdw-20260409-ha-mcp-migration`, phase 6 parallel-run), I initially claimed SmartHub's `tools/*.md` files were ~50% redundant with "ha-mcp's bundled skills." A verification pass uncovered a discovery (**D1**) that invalidates that premise: the ha-mcp 7.2.0 PyPI wheel ships **zero** bundled skill markdown files. This doc documents the real redundancy analysis — which is more modest than the original claim (~120-145 lines trimmable out of **951 total lines** in six suspect files) but still worth doing for latency reasons. Four findings total.

**Six suspect files enumerated** (verified via `wc -l` on 2026-04-10):
| File | Lines |
|---|---|
| `tools/_common.md` | 54 |
| `tools/_ha-mcp.md` | 45 |
| `tools/_services.md` | 85 |
| `tools/_errors.md` | 42 |
| `tools/automations/_reference.md` | 473 |
| `tools/integrations/_guide.md` | 252 |
| **Total** | **951** |

## Intent

**Goal:** Reduce LLM context tokens spent on redundant documentation so OpenClaw responds faster. Memory notes both beta users are complaining about latency and the bottleneck is LLM round-trips — every KB of redundant context cut is round-trip time saved. **The win here is modest, not transformative.**

**Priority ranking:** Correctness > latency > minimalism. Do NOT delete anything that could change OpenClaw's behavior or lose HA-specific knowledge. Tokens are cheap relative to broken UX.

**Decision boundaries:**
- Agent (Claude) may propose line-range cuts with evidence. User approves each batch before any deletion.
- Agent MAY delete whitespace, reformat redundant tables, and update cross-references in `TOOLS.md` after approval.
- Agent MUST NOT delete content that teaches HA-specific patterns, SmartHub operational rules, or historical migration context (prevents regression to old API patterns).
- Agent MUST NOT modify `docs/superpowers/specs/2026-04-09-ha-mcp-integration-design.md` (it's the historical record of the migration) — only append a correction note.

**Stop rules:**
- If a section marked "redundant" on inspection turns out to contain quirks, edge cases, or operational rules, STOP the deletion for that section and reclassify as "keep."
- If git blame shows a "redundant" section was added specifically to compensate for a known LLM gap, KEEP it.
- If the proposed cut exceeds 25% of any single file, pause and re-verify with the user before proceeding (large cuts suggest mis-classification).
- If the total proposed savings drop below ~50 lines after refinement, STOP the entire workflow — it's not worth the churn. Report back and recommend option 3 (defer).

## Discovery D1 — ha-mcp 7.2.0 ships no bundled skills

**This is not a finding to "fix" but a fact that changes the analysis framing. Documented here so the issue doc is self-contained.**

The ha-mcp 7.2.0 wheel on PyPI (what SmartHub installs via `uvx ha-mcp@7.2.0`) does NOT contain the `resources/skills-vendor/skills/` directory referenced in ha-mcp's source code. The skills-vendor is a git submodule that gets stripped from the wheel build. Consequences:
- `server._get_skills_dir()` returns `None` (source: `ha_mcp/server.py:146`)
- `_register_skills()` logs a warning and exits without registering anything (source: `ha_mcp/server.py:471`)
- `_build_skills_instructions()` returns `None`, so the MCP server instructions are empty
- `ListMcpResourcesTool` for the `ha-mcp` server returns "No resources found" — confirmed at runtime
- The `ENABLE_SKILLS=true` and `ENABLE_SKILLS_AS_TOOLS=true` env vars in `.claude/settings.json` have no effect because there are no skills to load

**Evidence:**
- Wheel `RECORD` at `~/.cache/uv/archive-v0/*/lib/python3.13/site-packages/ha_mcp-7.2.0.dist-info/RECORD` contains no `.md` files and no `resources/` directory entries (only `ha_mcp/tools/tools_resources.py` which is unrelated — it's about dashboard custom cards)
- Two independent archive-v0 hash dirs both confirm the missing `resources/` — not a corruption
- Zero `SKILL.md` files anywhere in `~/.cache/uv`

**Upstream implication:** This is probably a ha-mcp packaging bug (the code paths exist but can never fire). Out of scope for this workflow — note and move on.

**Impact on this audit:** The original claim that "ha-mcp's bundled skills make SmartHub's `_common.md`, `_services.md`, `_ha-mcp.md`, `_errors.md`, etc. mostly redundant" is **false**. The correct question is: does each file contain information beyond what the LLM can infer from raw MCP tool schemas alone? All findings below are scoped to *that* question.

---

## Findings

### P1: `tools/_ha-mcp.md` is fully redundant with ha-mcp tool schemas

**Severity:** Medium
**Category:** Context efficiency
**Affected components:** `tools/_ha-mcp.md` (45 lines), `TOOLS.md` (cross-references)

**Description:** Every row in every table in `tools/_ha-mcp.md` maps one-to-one to a ha-mcp tool name and its parameter names. The LLM already receives all of this via the MCP tool schema when the `ha-mcp` server is connected. The four tables (Device Control, Automation Management, Integration Management, Helpers) and the Tool Search section together add zero information beyond `tool_name: param, param, param` — which is exactly what the tool schema provides with `description` and `parameters` properties already populated.

Example — the file says:
```
| Turn on/off | ha_call_service | domain, service, entity_id |
```
The tool schema for `mcp__ha-mcp__ha_call_service` already has a `description` field and typed parameters with `Field(description=...)` for domain, service, and entity_id. Reading the schema gives the LLM strictly more information than the table row.

**The file is also actively wrong, not just redundant.** Line 19 references `ha_config_delete_automation`:
```
| Delete | `ha_config_delete_automation` | automation_id |
```
But the actual ha-mcp tool name is `ha_config_remove_automation` (confirmed via the live MCP tool list — no `ha_config_delete_automation` exists). If the LLM trusts this file over the live schema, it would attempt to call a nonexistent tool. This is the maintenance liability already materialized: the file was written before ha-mcp finalized its tool names and has silently gone stale.

**Impact:** 45 lines of context consumed on every OpenClaw invocation for zero informational gain, **plus one line that would actively mislead the LLM into calling a nonexistent tool**. Small latency tax and a maintenance liability that has already started breaking (stale tool name).

**Success criteria:**
- [ ] `tools/_ha-mcp.md` is deleted
- [ ] `TOOLS.md` no longer references `_ha-mcp.md`
- [ ] No other file in the repo references `tools/_ha-mcp.md` (verified via grep)
- [ ] A smoke-test conversation (e.g., "turn on the TV") succeeds without the file
- [ ] The ha-mcp tool list is still discoverable to the LLM via normal MCP introspection

---

### P2: `tools/_common.md` lines 10-48 duplicate ha-mcp tool schemas

**Severity:** Low
**Category:** Context efficiency
**Affected components:** `tools/_common.md` (54 lines total)

**Description:** Lines 10-48 of `tools/_common.md` are "Commonly Used Tools" — six fenced code blocks showing the tool name and parameter names for `ha_search_entities`, `ha_get_state`, `ha_call_service`, `ha_get_areas`, `ha_config_entries_get`, and `ha_search_tools`. Every one of these is a verbatim restatement of the tool schema the LLM already receives.

Lines 1-8 and 50-54 are **not** redundant and must be preserved:
- **Lines 3-8** contain historical migration context ("All HA interaction goes through ha-mcp tools... No curl. No API routing. No ports to configure.") and an auth note ("ha-mcp handles authentication internally via HOMEASSISTANT_TOKEN env var"). The "no curl" line prevents regression — without it, a future LLM run might try to fall back to the pre-migration curl pattern it read in git history.
- **Lines 50-54** contain SmartHub-specific network info (`homeassistant.local:<HA_PORT>`, mDNS resolution pattern, `.env` port lookup). None of this is in any tool schema.

**Impact:** ~38 lines of context consumed for zero informational gain per OpenClaw invocation.

**Success criteria:**
- [ ] `tools/_common.md` lines 10-48 are removed
- [ ] `tools/_common.md` lines 3-8 and 50-54 are preserved verbatim (header + network info + auth note + "no curl" historical note)
- [ ] A smoke-test conversation that requires tool discovery (e.g., "what devices do I have in the living room?") still works
- [ ] `TOOLS.md` references to `_common.md` still resolve to a valid file

---

### P3: `tools/_services.md` tables duplicate `ha_list_services` but embed load-bearing quirk notes

**Severity:** Low
**Category:** Context efficiency + quirk preservation
**Affected components:** `tools/_services.md` (85 lines total)

**Description:** Eight domain-service tables (lines 5-74) that list service names and data fields — most of this output is available at runtime via `ha_list_services(domain="light")` etc. **However**, the "Notes" column of several rows contains HA-specific knowledge the LLM cannot derive from the schema alone:
- Line 28: `set_hvac_mode` — "States ARE HVAC modes, not on/off" — teaches the LLM that `climate.*` entity state is the HVAC mode string, not a boolean. Without this, the LLM will misinterpret state reads.
- Line 36: `media_player.turn_on` — "May not work if device disconnects Wi-Fi in standby" — device quirk note. Prevents wasted retries.
- Line 47: `select_source` — "Check entity attributes for available sources" — pattern reinforcement.
- Lines 76-85: "Brightness Conversion" — critical pattern ("HA brightness is 0-255, not 0-100%") + user-phrased lookup table (25%/50%/75%/100% → brightness value). This is the canonical place the LLM learns to translate natural language to HA parameters.

**The simple "delete the tables" approach would strip these quirks.** The correct refinement is a finer cut: delete the `Service` and `Data fields` columns (pure schema duplication) but preserve any row that has non-empty Notes content, consolidated into a "Quirks & Patterns" section.

**Impact:** ~50 lines of context are genuinely trimmable after extracting quirks; ~25-30 lines are quirks + brightness conversion + section structure that must remain.

**Quirks inventory — every string below MUST survive the restructure and grep-match in the rewritten file:**
- `"States ARE HVAC modes"` (climate quirk, current line 28)
- `"May not work if device disconnects Wi-Fi in standby"` (media_player turn_on quirk, current line 36)
- `"Check entity attributes for available sources"` (select_source pattern, current line 47)
- `"Check entity attributes for available options"` (select.select_option pattern, current line 53)
- `"Check entity attributes for min/max/step"` (number.set_value pattern, current line 59)
- `"Brightness in HA is 0-255, not 0-100%"` (brightness conversion rule, current line 78)
- `"brightness = percentage × 2.55"` (brightness conversion formula, current line 78)
- The percentage→brightness lookup table rows (25%→64, 50%→128, 75%→191, 100%→255, current lines 82-85)

**Success criteria:**
- [ ] `tools/_services.md` is restructured to contain ONLY the Brightness Conversion section, the quirks listed in the inventory above (consolidated into a single "Quirks & Patterns" section), and a one-liner pointer to `ha_list_services` for the full service catalog
- [ ] Every string in the Quirks inventory grep-matches in the rewritten file (`grep -F "<string>" tools/_services.md` exits 0 for each; run as a single compound check)
- [ ] The rewritten `tools/_services.md` is ≤ 30 lines (aggressive target; if larger, re-review before committing)
- [ ] A smoke-test conversation "set AC to 24 degrees" succeeds (confirms HVAC mode quirk still teachable)
- [ ] A smoke-test conversation "dim lights to 50%" succeeds (confirms brightness conversion still teachable)
- [ ] A smoke-test conversation "turn on the TV" succeeds (confirms media_player standby quirk still teachable — device may be in standby)

---

### P4: Migration design doc asserts bundled skills but wheel ships none

**Severity:** Low
**Category:** Documentation accuracy
**Affected components:** `docs/superpowers/specs/2026-04-09-ha-mcp-integration-design.md` — primary passage "ha-mcp skills vs our skill files" at **lines 496-504**. Secondary references also at line 58 ("Skill files in `tools/` for device-specific knowledge"), lines 120-121 (ENABLE_SKILLS / ENABLE_SKILLS_AS_TOOLS env var docs describing "HA best-practice knowledge"), and line 472 (inventory row listing `tools/_ha-mcp.md` as a skill file). The correction note should reference all four locations but only amend lines 496-504 directly; the others are contextually correct about OpenClaw's own files.

**Description:** The ha-mcp migration design doc, lines 496-504, asserts: *"ha-mcp bundles general HA best-practice skills (automation patterns, helper selection, etc.). Our `tools/` files have device-specific knowledge... They complement each other: **ha-mcp skills**: how to use HA properly (general); **Our skill files**: what we know about specific devices (specific). Keep both. No conflict. No deduplication needed."* Discovery D1 shows this is false for the shipped PyPI wheel — ha-mcp 7.2.0 ships zero bundled skills. A future contributor reading this doc would form a wrong mental model and might make architectural decisions based on a capability that doesn't exist.

**Impact:** Low — the doc is a historical record, not actively consulted for current behavior. But it's a landmine for anyone revisiting the migration.

**Success criteria:**
- [ ] A correction note is appended (not inline-edited) to `docs/superpowers/specs/2026-04-09-ha-mcp-integration-design.md` explaining that ha-mcp 7.2.0 PyPI wheel does not include the skills-vendor submodule
- [ ] The note references Discovery D1 in `docs/rdw-state-skill-audit.json` for full evidence
- [ ] The note is dated 2026-04-10 and attributed to this audit workflow
- [ ] The original doc content is preserved (append, don't rewrite — it's historical)

---

## Workflow Completion Criteria

Stage 3 (implementation) is complete when ALL of these gates pass. These are the objective checks that tie per-finding success criteria back to the Intent goal:

**Baseline to record before any cuts** (append to `rdw-state-skill-audit.json` under `discoveries` as D2):
- `wc -l` output for all six suspect files (expected: 951 total, per Summary table)
- `stat -c '%s' tools/_common.md tools/_ha-mcp.md tools/_services.md` output (byte sizes of the three files touched by P1/P2/P3)

**Completion gates:**
- [ ] Total lines removed across P1 + P2 + P3 ≥ 100 lines (lower bound; target ~120-145 per the trimmable estimate)
- [ ] Byte-size delta (pre-cut minus post-cut) of the three touched files ≥ 3 KB of pure content reduction
- [ ] P4 success criteria all checked (design-doc correction note appended)
- [ ] Three post-cut smoke tests all succeed on a live SmartHub session:
  - [ ] "turn on the TV" — exercises tool discovery after `_common.md` trim and `_ha-mcp.md` deletion
  - [ ] "dim lights to 50%" — exercises brightness conversion, confirms P3 quirks survived
  - [ ] "set AC to 24 degrees" — exercises HVAC mode quirk, confirms P3 quirks survived
- [ ] No regression in tool-call outputs for OpenClaw's existing example prompts (spot-check 3 prompts from `.superpowers/` if any exist; otherwise manual replay of a recent beta user conversation)

**Abort condition:** If after Stage 2 planning the refined trim estimate drops below 50 lines total, STOP the workflow, report the finding, and recommend option 3 (defer). Not worth the churn.

## Accepted Residual Risks

**R1 — Dependence on ha-mcp tool schema stability.** Once we delete `_ha-mcp.md` and trim `_common.md`/`_services.md`, the LLM relies on ha-mcp's own tool descriptions for tool discovery. If ha-mcp renames `ha_call_service` to `ha_control_device` in a future version, OpenClaw will still work (MCP handles discovery) but any docs referencing the old name will be stale. *Rationale to accept:* We already depend on ha-mcp schema stability for everything the tools do — this just extends that dependency slightly.

**R2 — Modest savings, not transformative.** The total trimmable content is ~80-120 lines out of ~894 lines in the six suspect files. Context savings ≈ 3-5 KB, round-trip latency improvement likely in the 50-200 ms range (back-of-envelope, unmeasured). This is NOT the ~50% cut the original audit claimed. *Rationale to accept:* Beta users are already complaining; even small wins are worth shipping if the cost is low. If after this audit the measured latency improvement is sub-noticeable, we'll learn that latency has a different bottleneck and pivot.

**R3 — ha-mcp packaging bug left unreported.** The missing `resources/skills-vendor/` in the PyPI wheel is likely an upstream bug. Filing it would benefit other ha-mcp users. *Rationale to accept:* Out of scope for this workflow; track as a follow-up task, don't block on it.

## Dependencies Between Findings

- **P1, P2, P3 are independent** — can be implemented in any order, any combination.
- **P4 is independent** — doc correction, no code touched.
- **P4 should be completed even if P1/P2/P3 are deferred** — the doc correction stands on its own merit and takes ~5 min.
- **No finding blocks another.**

## Files NOT Flagged for Any Change (Explicit Keep List)

For clarity, these files were analyzed and explicitly confirmed as load-bearing. Each row includes a "why not redundant" justification so a future reviewer can verify each Keep decision without re-running the audit.

| File | Lines | Analysis depth | Why not redundant with ha-mcp schemas |
|---|---|---|---|
| `CLAUDE.md` | ~94 | Full read | OpenClaw identity, rules, confirmation policy, markdown-link mandate. No equivalent in any ha-mcp schema. |
| `TOOLS.md` | ~97 | Full read | Router file with Quick Reference table. Cross-references Keep List files. Needs a minor edit after P1 to drop the `_ha-mcp.md` row. |
| `tools/setup.md` | 289 | Full read | SmartHub install/smoke-test flow, `.env` setup, Docker bootstrap. ha-mcp has no install-flow equivalent. |
| `tools/_errors.md` | 42 | Full read | Error recovery patterns + SmartHub Docker workflows, 0% schema duplication. **Note: line 27 contains a historical meta-note — "The old 'Port conflict' row (referencing Step 3b) is intentionally removed" — preserved as a regression prevention anchor. Do NOT delete this line; it prevents a future LLM from reintroducing a port conflict entry.** |
| `tools/automations/_guide.md` | 222 | Full read | SmartHub's automation workflow, required-details checklist, confirmation rules. Pure operational workflow; nothing in ha-mcp schemas. |
| `tools/automations/_reference.md` | 473 | Spot-checked (trigger/condition/action sections) | HA automation JSON reference with ~13 trigger platforms, condition types, action types, example templates. `ha_config_set_automation`'s parameter doc says "config: Complete automation configuration with required fields: alias, trigger, action" — it does NOT enumerate trigger platforms, field names, or example JSON. **Audit depth caveat:** not verified line-by-line; if a deeper pass reveals schema-duplicating content, file a discovery and add a finding. |
| `tools/integrations/_guide.md` | 252 | Spot-checked (workflow + OAuth/mDNS sections) | SmartHub workflow order, HACS silent-install rule, mandatory dashboard-link rule, OAuth redirect + mDNS troubleshooting. ~50% SmartHub operational rules + ~30% HA-generic patterns not in tool schemas. **Audit depth caveat:** the guided setup section (lines 130-233) was not cross-checked against ha-mcp config-flow tool docstrings line-by-line. Follow-up verification recommended if Stage 3 latency measurements suggest further trimming would help. |
| `tools/xiaomi-home/*` | ~305 (4 files) | Full read of each | Device-specific quirks, entity patterns, OAuth cloud regions for the user's actual hardware. Not in any schema — hardware-specific knowledge that the ha-mcp Xiaomi integration docs don't cover. |
| `tools/printer/office-printer.md` | 52 | Full read | User's actual printer setup. Hardware-specific. |
| `tools/automations/tv_off_*.md` | ~45 (3 files) | Full read | User's actual automations — state record of what's deployed, not generic docs. |

**Known audit-depth caveats:** The analysis focused heavily on the six suspect files (P1-P3 targets) where redundancy was most likely. The Keep List files were spot-checked rather than exhaustively line-audited. If Stage 3 implementation discovers schema duplication in a Keep List file, treat it as a new discovery (RDW Stage 3 discovery protocol) and append a P5 finding rather than acting silently. In particular, `automations/_reference.md` (473 lines) and `integrations/_guide.md` (252 lines) together account for ~76% of the Keep List's 951-line "suspect files" bulk, so a deeper pass on those is the highest-yield follow-up if further latency reduction is needed.
