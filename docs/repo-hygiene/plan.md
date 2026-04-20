# Repo Hygiene Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove dead legacy surfaces and reorganize the repo so it matches the current `ha-mcp` architecture without trampling unrelated in-progress edits.

**Architecture:** Use an evidence-first cleanup. Phase 1 proves `api/` is not wired into the active runtime before deletion and clears the abandoned `harness/` residue. Phase 2 resolves workspace scaffolding files while respecting `AGENTS.md`. Phase 3 separates live docs from historical artifacts and removes stale architecture claims from current-facing docs. Every phase ends with grep- or test-based verification.

**Tech Stack:** Git, Bash, Markdown, apply_patch, tracked file deletes, workspace-safe trash/delete utilities, focused pytest checks

---

### Task 1: Verify and remove legacy backend surfaces

**Files:**
- Delete: `api/Dockerfile`
- Delete: `api/package.json`
- Delete: `api/src/device-aggregator.ts`
- Delete: `api/src/ha-client.ts`
- Delete: `api/src/index.ts`
- Delete: `api/src/routes/areas.ts`
- Delete: `api/src/routes/camera.ts`
- Delete: `api/src/routes/chat.ts`
- Delete: `api/src/routes/devices.ts`
- Delete: `api/src/routes/services.ts`
- Delete: `api/src/routes/xiaomi.ts`
- Delete: `api/src/types.ts`
- Delete: `api/tsconfig.json`
- Remove local residue: `harness/`
- Modify: `docs/repo-hygiene/rdw-state.json`

- [ ] **Step 1: Re-run the active-runtime reference grep before deleting anything**

```bash
git grep -n "API_PORT\|localhost:3001\|/api/devices\|SmartHub API\|Elysia" -- \
  README.md CLAUDE.md TOOLS.md install.sh scripts tests tools \
  docker-compose.yml docker-compose.linux.yml docker-compose.macos.yml \
  .claude .env.example ':!docs/**'
```

Expected: no matches. If any active-runtime match appears, stop and reassess before deleting `api/`.

- [ ] **Step 2: Re-check the current entry points to confirm there is no backend service wiring**

```bash
sed -n '1,160p' docker-compose.yml
sed -n '1,160p' docker-compose.linux.yml
sed -n '1,160p' docker-compose.macos.yml
sed -n '1,260p' install.sh
```

Expected: only Home Assistant and `ha-mcp` wiring remain; no service or bootstrap step refers to `api/`.

- [ ] **Step 3: Delete the tracked `api/` subtree with `apply_patch`**

```diff
*** Delete File: api/Dockerfile
*** Delete File: api/package.json
*** Delete File: api/src/device-aggregator.ts
*** Delete File: api/src/ha-client.ts
*** Delete File: api/src/index.ts
*** Delete File: api/src/routes/areas.ts
*** Delete File: api/src/routes/camera.ts
*** Delete File: api/src/routes/chat.ts
*** Delete File: api/src/routes/devices.ts
*** Delete File: api/src/routes/services.ts
*** Delete File: api/src/routes/xiaomi.ts
*** Delete File: api/src/types.ts
*** Delete File: api/tsconfig.json
```

- [ ] **Step 4: Remove the abandoned local `harness/` residue**

```bash
trash harness
```

Fallback if `trash` is unavailable: check for `gio trash harness`. If neither exists, stop and ask before using a destructive alternative.

- [ ] **Step 5: Verify the legacy backend surfaces are gone**

```bash
test ! -e api
git status --short harness
test ! -e harness
```

Expected: the `api/` and `harness/` directories are gone from the workspace, with no residual `harness` status entry.

### Task 2: Remove unused identity scaffolding without breaking the reusable template flow

**Files:**
- Delete: `IDENTITY.md`
- Modify: `docs/repo-hygiene/rdw-state.json`

- [ ] **Step 1: Re-read the workspace startup contract before touching identity files**

```bash
sed -n '1,120p' AGENTS.md
sed -n '1,120p' USER.md
sed -n '1,120p' IDENTITY.md
```

Expected: confirm `AGENTS.md` requires `USER.md` at session startup, while `IDENTITY.md` is optional workspace scaffolding.

- [ ] **Step 2: Delete `IDENTITY.md` if it has no active workspace contract**

```diff
*** Delete File: IDENTITY.md
```

- [ ] **Step 3: Leave `USER.md` in place as a reusable public template**

```bash
sed -n '1,120p' USER.md
```

Expected: `USER.md` remains present and generic because the repo is meant for others to copy and fill in.

- [ ] **Step 4: Verify the root no longer contains the unused identity scaffold**

```bash
test ! -f IDENTITY.md
test -f USER.md
```

Expected: `IDENTITY.md` is gone and `USER.md` remains.

### Task 3: Separate live docs from history and remove stale architecture claims

**Files:**
- Create: `docs/archive/`
- Move: historical workflow and strategy docs from top-level `docs/` into `docs/archive/`
- Modify: `README.md`
- Modify: `docs/fix-checklist.md`
- Modify: `docs/index.html` if it links to moved files
- Modify: `docs/repo-hygiene/rdw-state.json`

- [ ] **Step 1: Classify top-level docs into live vs historical without restoring already deleted files**

```bash
find docs -maxdepth 1 -type f | sort
git status --short docs
```

Expected: identify existing top-level files only, and preserve the current deletions of `docs/known-issues.md`, `docs/onepager.md`, and `docs/research.md`.

- [ ] **Step 2: Create an explicit archive directory and move historical artifacts under it**

```text
Move examples:
- docs/rdw-p0-issue-doc.md -> docs/archive/rdw/rdw-p0-issue-doc.md
- docs/rdw-p0-plan.md -> docs/archive/rdw/rdw-p0-plan.md
- docs/rdw-p0-validation.md -> docs/archive/rdw/rdw-p0-validation.md
- docs/rdw-p1-5-9-issue-doc.md -> docs/archive/rdw/rdw-p1-5-9-issue-doc.md
- docs/rdw-p1-5-9-plan.md -> docs/archive/rdw/rdw-p1-5-9-plan.md
- docs/rdw-p1-5-9-validation-report.md -> docs/archive/rdw/rdw-p1-5-9-validation-report.md
- docs/rdw-*.json -> docs/archive/rdw/
- docs/macos-*-issue-doc.md -> docs/archive/incidents/
- docs/macos-*-validation-report.md -> docs/archive/incidents/
- docs/openclaw-install-recovery-*.md -> docs/archive/incidents/
- docs/minimalist-review.md -> docs/archive/strategy/minimalist-review.md
- docs/go-to-market-playbook.md -> docs/archive/strategy/go-to-market-playbook.md
- docs/market-research-prompt.md -> docs/archive/strategy/market-research-prompt.md
- docs/issue-positioning-and-differentiation.md -> docs/archive/strategy/issue-positioning-and-differentiation.md
```

Keep live docs such as `feedback.md`, `fix-checklist.md`, `index.html`, and media assets in place.

- [ ] **Step 3: Remove stale architecture claims from current-facing docs**

```bash
git grep -n "Bun/Elysia API\|SmartHub API\|frontend harness" -- README.md docs/feedback.md docs/fix-checklist.md docs/index.html
```

Expected: locate any remaining current-facing claims, then update or archive the owning file so the grep becomes clean.

- [ ] **Step 4: Mark the checklist cleanup items complete in the live tracker**

```markdown
Update docs/fix-checklist.md so items 14-17 reflect:
- `api/` removed after runtime verification
- `harness/` removed as abandoned local residue
- `IDENTITY.md` removed and `USER.md` populated
- historical docs moved under `docs/archive/`
```

- [ ] **Step 5: Verify the top-level docs tree now reflects live materials only**

```bash
find docs -maxdepth 1 -type f | sort
git grep -n "Bun/Elysia API\|SmartHub API\|frontend harness" -- README.md docs/feedback.md docs/fix-checklist.md docs/index.html
```

Expected: top-level `docs/` contains live materials plus the new archive directory, and the current-facing grep is clean.

### Task 4: Run focused validation and capture the workflow result

**Files:**
- Modify: `docs/repo-hygiene/rdw-state.json`
- Create: `docs/repo-hygiene/validation-report.md`

- [ ] **Step 1: Run focused repo-hygiene verification commands**

```bash
git grep -n "API_PORT\|localhost:3001\|/api/devices\|SmartHub API\|Elysia" -- \
  README.md CLAUDE.md TOOLS.md install.sh scripts tests tools \
  docker-compose.yml docker-compose.linux.yml docker-compose.macos.yml \
  .claude .env.example ':!docs/**'
git grep -n "Bun/Elysia API\|SmartHub API\|frontend harness" -- README.md docs/feedback.md docs/fix-checklist.md docs/index.html
test ! -e harness
test ! -f IDENTITY.md
test -f USER.md
```

Expected: all checks succeed with no output from the grep commands.

- [ ] **Step 2: Run focused regression tests for the setup and approval docs**

```bash
python3 -m pytest tests/test_setup_docs.py tests/test_approval_gate.py tests/test_integrations_docs.py -v
```

Expected: all selected tests pass.

- [ ] **Step 3: Write the validation report with command output evidence**

```markdown
# Validation Report

- Record each finding P1-P4
- Include the exact grep/test/pytest commands that were run
- Mark PASS/FAIL with actual results
```

- [ ] **Step 4: Update the workflow state to complete**

```json
{
  "current_stage": "complete",
  "stages_completed": ["document", "plan", "implement", "validate"]
}
```

## Self-Review

- Coverage check: Task 1 maps to P1-P2, Task 2 maps to P3, Task 3 maps to P4, and Task 4 validates all four findings.
- Placeholder scan: no `TODO`, `TBD`, or undefined file moves remain.
- Scope check: limited to P3 cleanup plus the required `api/` verification gate; no unrelated runtime changes are included.
