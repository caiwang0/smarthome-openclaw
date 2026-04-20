# Repo Hygiene Cleanup Issue Document

**Date:** 2026-04-20
**Scope:** P3 repo hygiene for the SmartHub repository, with explicit validation of whether the legacy `api/` subtree is still live before any deletion
**Analyst:** Codex via review-driven-workflow

## Summary

This audit checked whether the repository still matches the current `ha-mcp`-based architecture. Four findings remain: a tracked legacy `api/` subtree, an untracked `harness/` residue directory, placeholder identity files, and a `docs/` tree that mixes live materials with historical workflow artifacts and stale architecture claims.

Overall severity is medium. The risk is not runtime breakage by itself; the risk is that the repo still advertises dead components as current and keeps misleading future work anchored to retired architecture.

## Intent

**Goal:** Make the repository accurately reflect the current SmartHub architecture, remove dead legacy surfaces, and preserve only the historical context needed to explain major migrations.

**Priority ranking:** repo accuracy > avoiding accidental deletion of live dependencies > preserving historical artifacts > minimizing diff size

**Decision boundaries:** The agent may remove or archive components that have no live runtime, install, config, or test wiring; may reorganize docs and update current-facing docs to remove stale architecture claims; must stop and ask if any active dependency on a candidate deletion is found; must not revert unrelated user changes already present in the worktree.

**Stop rules:** Stop if `api/` is still referenced by active runtime files or required for current tests; stop if cleanup would conflict with unrelated pending user edits; stop if a workspace instruction requires a file that cleanup would remove without a compatible replacement.

## Findings

### P1: Legacy `api/` subtree is still tracked after the `ha-mcp` migration

**Severity:** Medium
**Category:** Architecture drift
**Affected components:** `api/`, `README.md`, historical planning/spec docs

**Description:** The repository still tracks a full Bun/Elysia HTTP service under `api/`, but the current runtime wiring no longer references it. `docker-compose*.yml` define only the Home Assistant service, `install.sh` bootstraps Home Assistant plus `ha-mcp`, and active config no longer uses `API_PORT`. Historical migration docs already describe `api/` as a temporary parallel-run holdover that should be removed once the `ha-mcp` path is verified.

**Impact:** Contributors can misread the architecture, spend effort maintaining dead code, or reintroduce obsolete flows because the repo still contains a plausible but unused backend.

**Success criteria:**
- [ ] `git grep -n "API_PORT\\|localhost:3001\\|/api/devices\\|SmartHub API\\|Elysia" -- README.md CLAUDE.md TOOLS.md install.sh scripts tests tools docker-compose.yml docker-compose.linux.yml docker-compose.macos.yml .claude .env.example ':!docs/**'` returns no active-runtime references to the legacy API.
- [ ] Current runtime/config entry points (`docker-compose*.yml`, `install.sh`, `.claude/settings*.json`, `.env.example`) do not depend on `api/`.
- [ ] `test ! -e api` succeeds after cleanup, and focused verification still passes.

---

### P2: `harness/` exists as local residue rather than a maintained repo component

**Severity:** Low
**Category:** Workspace hygiene
**Affected components:** `harness/`, docs that describe a frontend harness as current

**Description:** The working tree contains a `harness/` directory with `dist/`, `node_modules/`, `bun.lock`, and an empty `prompts/` directory, but no tracked source files. The tracked repo only mentions the harness in historical commentary and one approval-gate code comment. In its current form, `harness/` reads as abandoned experimental output rather than an intentional subsystem.

**Impact:** Local clutter obscures the actual maintained codebase and keeps outdated product shape assumptions alive in the docs.

**Success criteria:**
- [ ] `git status --short harness` returns nothing after cleanup.
- [ ] `test ! -e harness` succeeds after cleanup, unless a tracked and documented replacement source tree is intentionally created.
- [ ] `git grep -n "frontend harness\\|generator-evaluator harness" -- README.md docs/feedback.md docs/fix-checklist.md docs/index.html` returns no current-architecture claims.

---

### P3: Identity/context scaffolding is inconsistent with the repo's public-template intent

**Severity:** Low
**Category:** Workspace clarity
**Affected components:** `IDENTITY.md`, `USER.md`, `AGENTS.md`

**Description:** `IDENTITY.md` and `USER.md` both look like template scaffolding, but they do not serve the same purpose. The user clarified that this repo is being pushed to GitHub for other people to reuse, so `USER.md` is intentionally allowed to remain a generic fill-in template. `IDENTITY.md` still reads as unused first-run scaffolding and has no matching workspace requirement.

**Impact:** Future users cannot tell which file is an intentional public template and which file is abandoned scaffolding, so the repo keeps unnecessary noise at the root.

**Success criteria:**
- [ ] `IDENTITY.md` is removed if it has no active workspace contract.
- [ ] `USER.md` remains present so `AGENTS.md` startup expectations still hold.
- [ ] `USER.md` is left as an intentional public template rather than being replaced with guessed personal defaults.

---

### P4: `docs/` mixes live product docs with historical audit artifacts and stale architecture claims

**Severity:** Medium
**Category:** Documentation hygiene
**Affected components:** `docs/`, `README.md`, historical RDW artifacts, marketing/strategy docs

**Description:** The top-level `docs/` directory currently mixes live collateral (`feedback.md`, `fix-checklist.md`, landing assets) with issue docs, plans, validation reports, state files, and old strategy notes. Some tracked docs still describe the Bun/Elysia API or a frontend harness as part of the current product shape. The worktree also already has pending deletions for some docs, so cleanup has to preserve those deletions rather than resurrect them accidentally.

**Impact:** It is difficult to tell what is current, outdated messaging survives longer than the code it describes, and contributors risk editing historical artifacts as if they were active guidance.

**Success criteria:**
- [ ] Historical workflow artifacts (`rdw-*`, `*-issue-doc.md`, `*-plan.md`, `*-validation*.md`, `*-state*.json`) no longer live at the top level of `docs/`; they move under an explicit archive/history directory.
- [ ] `git grep -n "Bun/Elysia API\\|SmartHub API\\|frontend harness" -- README.md docs/feedback.md docs/fix-checklist.md docs/index.html` returns no current-facing architecture claims.
- [ ] Existing pending deletions or unrelated user edits in `docs/` remain preserved unless intentionally superseded.

## Accepted Residual Risks

- A small archived note about the `api/` to `ha-mcp` migration may remain if it helps explain historical references without pretending the backend is still supported.
- `USER.md` remains a generic template file because the repo is intended for other users to copy and fill in.

## Dependencies Between Findings

- P1 informs P4 because current-facing docs cannot be cleaned accurately until the fate of `api/` is confirmed.
- P3 is constrained by `AGENTS.md`, which requires `USER.md` to remain present even though it is intentionally generic.
