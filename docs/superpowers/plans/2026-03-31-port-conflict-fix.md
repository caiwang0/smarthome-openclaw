# Port Conflict Fix — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace all hardcoded `localhost:3001` in functional files with dynamic `${API_PORT}` reads from `.env`.

**Architecture:** Every curl block that hits the SmartHub API gets a one-line preamble reading `API_PORT` from `.env`. The common file (`tools/_common.md`) establishes the pattern; all other files follow it. No runtime code or Docker config changes.

**Tech Stack:** Markdown skill files, bash variable expansion

**Issue doc:** `docs/issue-3-port-conflicts.md` (findings P1–P6)

---

## Phase 1: Establish the pattern in `tools/_common.md` (P1 + P6)

### Task 1: Add preamble and replace all hardcoded ports in `tools/_common.md`

**Files:**
- Modify: `tools/_common.md`

- [ ] **Step 1: Add "Read ports first" preamble at the top of the SmartHub API section**

Replace lines 1-5:
```markdown
# Common — Shared API & Network Reference

## SmartHub API (convenience layer)

Base URL: `http://localhost:3001`
```

With:
```markdown
# Common — Shared API & Network Reference

> **Before running any command below**, read the API port from `.env`:
> ```bash
> API_PORT=$(grep API_PORT .env | cut -d= -f2)
> ```
> All curl examples below use `${API_PORT}`. Never hardcode port 3001 — it may differ per installation.

## SmartHub API (convenience layer)

Base URL: `http://localhost:${API_PORT}`
```

- [ ] **Step 2: Replace all `localhost:3001` in curl examples**

Replace every `http://localhost:3001` with `http://localhost:${API_PORT}` in the file. There are 5 remaining occurrences after the Base URL (lines 9, 14, 19, 36).

The curl blocks become:
```bash
curl -s http://localhost:${API_PORT}/api/devices | jq '.devices[] | {name, device_type, status, area_name, primary_entity}'
```
```bash
curl -s http://localhost:${API_PORT}/api/devices/<device_id>
```
```bash
curl -s -X POST http://localhost:${API_PORT}/api/services/<domain>/<service> \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "<entity_id>"}'
```
```bash
curl -s http://localhost:${API_PORT}/api/areas | jq '.areas'
```

- [ ] **Step 3: Update Network Info section**

Replace line 100:
```markdown
- SmartHub API: `http://localhost:3001`
```
With:
```markdown
- SmartHub API: `http://localhost:${API_PORT}` (read `API_PORT` from `.env`; default 3001)
```

- [ ] **Step 4: Verify no `localhost:3001` remains**

Run: `grep -n 'localhost:3001' tools/_common.md`
Expected: No output (zero matches).

- [ ] **Step 5: Commit**

```bash
git add tools/_common.md
git commit -m "fix(tools): replace hardcoded port 3001 with dynamic API_PORT in _common.md

Adds a preamble instructing readers to read API_PORT from .env before
any API call. All curl examples now use \${API_PORT} variable.

Fixes part of #3"
```

---

## Phase 2: Propagate pattern to remaining files (P2–P5, P6)

### Task 2: Replace all hardcoded ports in `tools/xiaomi-home/tv.md`

**Files:**
- Modify: `tools/xiaomi-home/tv.md`

- [ ] **Step 1: Replace all 7 occurrences of `localhost:3001`**

Use replace-all to change every `http://localhost:3001` to `http://localhost:${API_PORT}` in the file.

After replacement, the Commands section curl blocks look like:
```bash
# Turn off (standby)
curl -s -X POST http://localhost:${API_PORT}/api/services/media_player/turn_off \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "<entity_id>"}'
```
(Same pattern for all 7 curl commands: volume_up, volume_down, volume_set, volume_mute, media_play, media_pause.)

- [ ] **Step 2: Verify no `localhost:3001` remains**

Run: `grep -n 'localhost:3001' tools/xiaomi-home/tv.md`
Expected: No output.

---

### Task 3: Replace hardcoded ports in `tools/setup.md`

**Files:**
- Modify: `tools/setup.md`

- [ ] **Step 1: Fix Step 8 health check (line 203)**

Replace:
```bash
curl -s http://localhost:3001/api/health
```
With:
```bash
API_PORT=$(grep API_PORT .env | cut -d= -f2)
curl -s http://localhost:${API_PORT}/api/health
```

- [ ] **Step 2: Fix Step 9 device verification (line 215)**

Replace:
```bash
curl -s http://localhost:3001/api/devices
```
With:
```bash
API_PORT=$(grep API_PORT .env | cut -d= -f2)
curl -s http://localhost:${API_PORT}/api/devices
```

- [ ] **Step 3: Strengthen Step 3b instruction for updating skill files**

At the end of the "If the API port is in use" section (after line 106), the existing text says:
```markdown
- Also update `tools/_common.md` to reflect the new port.
```

Replace with:
```markdown
- **Important:** If you assigned a non-default port, update all functional skill files that reference the API port. Run `grep -rn 'localhost:3001' tools/ CLAUDE.md TOOLS.md` and replace any remaining `localhost:3001` with `localhost:${API_PORT}` using the port you just assigned.
```

- [ ] **Step 4: Verify no `localhost:3001` remains**

Run: `grep -n 'localhost:3001' tools/setup.md`
Expected: No output.

---

### Task 4: Replace hardcoded ports in `CLAUDE.md`

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Fix first-run health check (line 18)**

Replace:
```bash
curl -s --max-time 5 http://localhost:3001/api/health 2>/dev/null | grep -q "ok" && echo "API_OK" || echo "API_DOWN"
```
With:
```bash
API_PORT=$(grep API_PORT .env | cut -d= -f2); curl -s --max-time 5 http://localhost:${API_PORT}/api/health 2>/dev/null | grep -q "ok" && echo "API_OK" || echo "API_DOWN"
```

- [ ] **Step 2: Fix post-integration device listing (line 167)**

Replace:
```bash
curl -s http://localhost:3001/api/devices
```
With:
```bash
API_PORT=$(grep API_PORT .env | cut -d= -f2); curl -s http://localhost:${API_PORT}/api/devices
```

- [ ] **Step 3: Verify no `localhost:3001` remains**

Run: `grep -n 'localhost:3001' CLAUDE.md`
Expected: No output.

---

### Task 5: Replace hardcoded port in `TOOLS.md`

**Files:**
- Modify: `TOOLS.md`

- [ ] **Step 1: Fix auto-generation curl command (line 94)**

Replace:
```markdown
1. Query `curl -s http://localhost:3001/api/devices` to discover new devices
```
With:
```markdown
1. Query `API_PORT=$(grep API_PORT .env | cut -d= -f2); curl -s http://localhost:${API_PORT}/api/devices` to discover new devices
```

- [ ] **Step 2: Update skill file template to include API_PORT pattern**

In the skill file template section (around line 138), replace:
```markdown
## Commands

<curl examples for each applicable service>
```
With:
```markdown
## Commands

> Read the API port first: `API_PORT=$(grep API_PORT .env | cut -d= -f2)`

<curl examples using http://localhost:${API_PORT}/api/services/...>
```

- [ ] **Step 3: Verify no `localhost:3001` remains**

Run: `grep -n 'localhost:3001' TOOLS.md`
Expected: No output.

---

### Task 6: Commit all Phase 2 changes

- [ ] **Step 1: Commit**

```bash
git add tools/xiaomi-home/tv.md tools/setup.md CLAUDE.md TOOLS.md
git commit -m "fix: replace all hardcoded port 3001 with dynamic API_PORT reads

Updates tv.md, setup.md, CLAUDE.md, and TOOLS.md to read API_PORT
from .env instead of assuming port 3001. Updates skill file template
to prevent future hardcoding.

Fixes #3"
```

---

## Phase 3: Final Verification

### Task 7: Run completion check

- [ ] **Step 1: Verify zero hardcoded ports remain in functional files**

Run: `grep -rn 'localhost:3001' tools/ CLAUDE.md TOOLS.md`
Expected: No output (zero matches).

- [ ] **Step 2: Verify `.env` still has the default**

Run: `grep API_PORT .env`
Expected: `API_PORT=3001` (unchanged — we only changed how files *read* it, not the value itself).
