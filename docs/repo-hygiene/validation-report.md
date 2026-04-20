# Validation Report

**Date:** 2026-04-20
**Issue document:** `docs/repo-hygiene/issue-doc.md`
**Total findings:** 4
**Passed:** 4 | **Failed:** 0 | **Skipped:** 0

## Results

### P1: Legacy `api/` subtree is still tracked after the `ha-mcp` migration - PASS

- [x] Criterion 1
  Evidence: Ran
  `git grep -n "API_PORT\|localhost:3001\|/api/devices\|SmartHub API\|Elysia" -- README.md CLAUDE.md TOOLS.md install.sh scripts tests tools docker-compose.yml docker-compose.linux.yml docker-compose.macos.yml .claude .env.example ':!docs/**'`
  Output: no matches
  Exit code: `1`
  Verdict: PASS - the active runtime/config surface no longer references the legacy API.

- [x] Criterion 2
  Evidence: The same active-runtime grep covered `docker-compose*.yml`, `install.sh`, `.claude`, and `.env.example` with no matches. Earlier direct inspection of `docker-compose*.yml`, `.env.example`, and `.claude/settings.json` showed only Home Assistant and `ha-mcp` wiring.
  Verdict: PASS - current runtime/config entry points do not depend on `api/`.

- [x] Criterion 3
  Evidence:
  - `test ! -e api` succeeded
  - Focused verification command:
    `./.venv/bin/python -m pytest tests/test_setup_docs.py tests/test_approval_gate.py tests/test_integrations_docs.py -v`
  Output: `11 passed in 0.24s`
  Verdict: PASS - `api/` is gone from the workspace and the focused regression suite still passes.

### P2: `harness/` exists as local residue rather than a maintained repo component - PASS

- [x] Criterion 1
  Evidence: Ran `git status --short harness`
  Output: no output
  Exit code: `0`
  Verdict: PASS - no `harness/` residue remains in git status.

- [x] Criterion 2
  Evidence: Combined existence check output:
  `HARNESS_REMOVED`
  Verdict: PASS - `test ! -e harness` succeeded and the residue directory is gone.

- [x] Criterion 3
  Evidence: Ran
  `git grep -n "frontend harness\|generator-evaluator harness" -- README.md docs/feedback.md docs/fix-checklist.md docs/index.html`
  Output: no matches
  Exit code: `1`
  Verdict: PASS - current-facing docs no longer present the harness as active architecture.

### P3: Identity/context scaffolding is inconsistent with the repo's public-template intent - PASS

- [x] Criterion 1
  Evidence: Combined existence check output:
  `IDENTITY_REMOVED`
  Verdict: PASS - `IDENTITY.md` has been removed from the workspace.

- [x] Criterion 2
  Evidence: Combined existence check output:
  `USER_PRESENT`
  Verdict: PASS - `USER.md` remains present, so the `AGENTS.md` startup contract still holds.

- [x] Criterion 3
  Evidence: Inspected `USER.md` after the user clarified the repo is meant for reuse.
  Output: `USER.md` remains the original generic fill-in template rather than guessed personal defaults.
  Verdict: PASS - the file stays intentionally reusable for downstream users.

### P4: `docs/` mixes live product docs with historical audit artifacts and stale architecture claims - PASS

- [x] Criterion 1
  Evidence: Ran `find docs -maxdepth 1 -type f | sort`
  Output:
  - `docs/cmd-paste-command.png`
  - `docs/cmd-run-as-admin.png`
  - `docs/example-review.png`
  - `docs/feedback.md`
  - `docs/fix-checklist.md`
  - `docs/index.html`
  Verdict: PASS - top-level `docs/` now exposes only live files and assets, while historical material lives under `docs/archive/`.

- [x] Criterion 2
  Evidence: Ran
  `git grep -n "Bun/Elysia API\|SmartHub API\|frontend harness\|generator-evaluator harness" -- README.md docs/feedback.md docs/fix-checklist.md docs/index.html`
  Output: no matches
  Exit code: `1`
  Verdict: PASS - current-facing docs are clean of stale backend/harness claims.

- [x] Criterion 3
  Evidence: Ran `git status --short docs | sed -n '1,80p'`
  Output included:
  - ` D docs/known-issues.md`
  - ` D docs/onepager.md`
  - ` D docs/research.md`
  - `?? docs/archive/`
  Verdict: PASS - the pre-existing deleted docs stayed deleted, and the archive move did not resurrect them.

## Accepted Residual Risks

- `USER.md` remains a generic template because the repo is intended for other users to copy and fill in.
- Historical context for the `api/` to `ha-mcp` migration remains available under `docs/archive/` and `docs/superpowers/`.

## New Issues Discovered

- None.

## Verdict

ALL PASS. The repo hygiene cleanup meets the four findings in the issue document with fresh verification evidence.
