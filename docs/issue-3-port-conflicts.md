# Port Conflict Detection & Hardcoded Port Removal

**Date:** 2026-03-31
**Scope:** All functional files referencing hardcoded `localhost:3001` (SmartHub API port)
**Source:** [GitHub Issue #3](https://github.com/caiwang0/smarthome-openclaw/issues/3)

## Summary

The SmartHub API port (3001) is hardcoded across 5 functional files. If the setup skill assigns a different port due to a conflict, all skill files and system instructions still point to the wrong port. The setup skill already detects port conflicts (Step 3b) but doesn't propagate the new port to dependent files. Additionally, the setup skill's own health-check and verification steps use hardcoded 3001 instead of reading from `.env`.

## Intent

**Goal:** Make the system resilient to non-default API port assignments so that any port configured in `.env` is used consistently everywhere.
**Priority ranking:** Correctness > Simplicity > Minimal diff (prefer a clean pattern over preserving the most lines unchanged)
**Decision boundaries:** Agent can edit all files listed below autonomously. No user input needed for text replacements.
**Stop rules:** Pause if a change would affect runtime code (`api/src/`), Docker config, or `.env` defaults. Work is complete when `grep -rn 'localhost:3001' tools/ CLAUDE.md TOOLS.md` returns zero results and all success-criteria checkboxes are checked.

## Findings

### P1: `tools/_common.md` — 6 hardcoded `localhost:3001` references

**Severity:** High
**Category:** Configuration
**Affected components:** `tools/_common.md` lines 5, 9, 14, 19, 36, 100

**Description:** The SmartHub API section has `http://localhost:3001` as a literal Base URL and in every curl example. The Network Info section also lists it literally. If `.env` has `API_PORT=3200`, every command the AI copies from this file will hit the wrong port.

**Impact:** AI agent sends all device commands to wrong port — complete loss of device control.

**Success criteria:**
- [ ] No literal `localhost:3001` remains in `tools/_common.md`
- [ ] A preamble instructs the reader to read `API_PORT` from `.env` before any call
- [ ] All curl examples use `${API_PORT}` variable
- [ ] Network Info section references the variable, not a literal port

---

### P2: `tools/xiaomi-home/tv.md` — 7 hardcoded `localhost:3001` references

**Severity:** High
**Category:** Configuration
**Affected components:** `tools/xiaomi-home/tv.md` lines 17, 25, 30, 35, 40, 48, 53

**Description:** Every curl command in the TV skill file uses `http://localhost:3001` literally.

**Impact:** TV commands (power, volume, playback) all fail if API port differs from 3001.

**Success criteria:**
- [ ] No literal `localhost:3001` remains in `tools/xiaomi-home/tv.md`
- [ ] All curl examples use `${API_PORT}` variable

---

### P3: `tools/setup.md` — 2 hardcoded `localhost:3001` references

**Severity:** Medium
**Category:** Configuration
**Affected components:** `tools/setup.md` lines 203, 215

**Description:** Steps 8 and 9 (health check and device verification) use `http://localhost:3001` literally, even though Step 3b already reads `API_PORT` from `.env` and may have changed it.

**Impact:** Setup verification fails if port was auto-reassigned in Step 3b — user thinks setup is broken when it's actually working on a different port.

**Success criteria:**
- [ ] Steps 8 and 9 read `API_PORT` from `.env` before making curl calls
- [ ] No literal `localhost:3001` remains in `tools/setup.md`

---

### P4: `CLAUDE.md` — 2 hardcoded `localhost:3001` references

**Severity:** High
**Category:** Configuration
**Affected components:** `CLAUDE.md` lines 18, 167

**Description:** The first-run health check (line 18) and the post-integration device listing (line 167) both use `http://localhost:3001` literally.

**Impact:** First-run check reports `API_DOWN` even when the API is running on a different port, triggering unnecessary setup flow. Post-integration verification also fails.

**Success criteria:**
- [ ] First-run check reads `API_PORT` from `.env`
- [ ] Post-integration device listing reads `API_PORT` from `.env`
- [ ] No literal `localhost:3001` remains in `CLAUDE.md`

---

### P5: `TOOLS.md` — 1 hardcoded `localhost:3001` reference

**Severity:** Medium
**Category:** Configuration
**Affected components:** `TOOLS.md` line 94

**Description:** The Skill Auto-Generation section tells the AI to run `curl -s http://localhost:3001/api/devices` after a new integration completes.

**Impact:** Auto-generated skill files won't discover new devices if port differs.

**Success criteria:**
- [ ] The curl command reads `API_PORT` from `.env`
- [ ] No literal `localhost:3001` remains in `TOOLS.md`

---

### P6: No standard preamble pattern across skill files

**Severity:** Low
**Category:** Consistency
**Affected components:** All files in `tools/`, `CLAUDE.md`, `TOOLS.md`

**Description:** There is no consistent convention for how skill files should reference the API port. Each file independently hardcodes it. A standard pattern (e.g., always read from `.env` at the top of a code block) would prevent this class of bug from recurring when new device skill files are auto-generated.

**Impact:** Future skill files will repeat the same hardcoding pattern unless the template and common file establish the convention.

**Success criteria:**
- [ ] `tools/_common.md` has a clear "Read ports first" instruction at the top
- [ ] The skill file template in `TOOLS.md` uses the dynamic pattern
- [ ] `tools/setup.md` Step 3b includes an explicit instruction to replace `localhost:3001` with `localhost:${API_PORT}` in all functional skill files when a non-default port is assigned

## Accepted Residual Risks

- **`localhost:8123` (HA port) remains hardcoded.** The issue explicitly scopes to port 3001 only. HA port 8123 is standard and cannot be easily reassigned (HA itself defaults to it). The issue notes HA port conflicts should block setup, not auto-reassign.
- **Historical docs (`docs/phase1-plan.md`, `docs/phase1-issues.md`, `docs/superpowers/`, `harness/`) not updated.** The issue explicitly excludes these. They are point-in-time records.

## Dependencies Between Findings

- P6 (standard preamble) should be addressed alongside P1 (common file) — the preamble goes into `_common.md`.
- P1 must be done before P2 — the TV file references should follow the same pattern established in `_common.md`.
- P3, P4, P5 are independent of each other but should follow the pattern from P1.
