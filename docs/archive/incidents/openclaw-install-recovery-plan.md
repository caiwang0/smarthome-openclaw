# OpenClaw Install Recovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the one-command OpenClaw install resume safely after interruption, keep `.env` and Home Assistant auth state synchronized, and force one shared non-destructive recovery path before the agent tells the user the flow is stuck.

**Architecture:** Keep bootstrap ownership in `install.sh`, but add a small on-disk checkpoint so seed, token write, and verification can resume in order without asking for a browser token again. Make `tools/_errors.md` the canonical recovery ladder and point setup/runtime/integration docs at it so every recoverable failure follows the same safe probe/retry/restart/resume sequence. Use targeted regression tests to lock in interrupted-install recovery, handoff continuation, and phase labeling.

**Tech Stack:** Bash, Python 3, Home Assistant markdown docs, `unittest`.

---

## Finding Map

- P1 -> Phase 1
- P2 -> Phase 2
- P3 -> Phase 2
- P4 -> Phase 3
- P5 -> Phase 4

## Phase 1: Resumable bootstrap state and token/env sync

**Scope:** `install.sh`, `scripts/seed-ha-storage.py`, `tests/test_install_sh.py`, `tests/test_seed_ha_storage.py`

**Goal of this phase:** A rerun after interruption can restore the bootstrap state and finish without requiring manual token retrieval, while still refusing destructive recovery.

- [ ] Add a root-only install checkpoint (`.openclaw-install-state.json`) in the repo root, with explicit phases for clone, patch, seed, token sync, and verification.
- [ ] Make `install.sh` write the checkpoint before seed starts, update it after seed succeeds, and clear it only after `.env` is synced and HA verification passes.
- [ ] Make the token write atomic: write to a temp file or temp copy first, then replace `.env` only after the token from the seed result is known to be present.
- [ ] Teach `install.sh` resume logic to detect the common interrupted case: seeded HA storage exists, the checkpoint says seed already completed, but `.env` still needs token sync.
- [ ] If `ha-config/.storage` is present but the checkpoint is missing or incomplete, stop before starting HA and route through the recovery ladder instead of trying to guess or destroying state.
- [ ] Keep `scripts/seed-ha-storage.py` strict about partial auth state, but make its failure path machine-readable enough for `install.sh` to distinguish `partial`, `complete`, and `fresh` cases without guessing.
- [ ] Leave the existing no-browser bootstrap intact for the first successful run; this phase is about replay safety, not changing the happy path flow.

**Verification:**

```bash
python3 -m unittest tests.test_seed_ha_storage tests.test_install_sh -v
```

Expected: existing idempotency tests still pass, and the new interrupted-install resume test confirms a rerun restores the token/env sync without printing a browser-token prompt.

## Phase 2: Post-install handoff unification and visible phase labels

**Scope:** `install.sh`, `CLAUDE.md`, `tools/setup.md`

**Goal of this phase:** The install-to-setup transition is one consistent handoff, and long installer phases are visibly labeled so OpenClaw does not look hung.

- [ ] Replace the soft text handoff at the end of `install.sh` with one canonical continuation message that tells the agent to proceed immediately into the setup/recovery flow in the repo directory.
- [ ] Update `CLAUDE.md` so the `install.sh` path and the setup path agree on the same post-install behavior instead of competing instructions.
- [ ] Rewrite the top of `tools/setup.md` so it no longer says it must only run when the user explicitly asks for setup help; it should also be the automatic continuation target after `install.sh`.
- [ ] Add visible start/completion/failure labels around each slow installer phase: clone, patch config, install uv, seed storage, sync token, verify ha-mcp, and handoff.
- [ ] Make failure output print the phase name before exit so a rerun can resume or debug from the right boundary.

**Verification:**

```bash
python3 -m unittest tests.test_install_sh -v
```

Expected: the install tests assert the handoff text is consistent, and a forced failure path reports the failing phase name instead of stopping silently.

## Phase 3: Single mandatory recovery ladder across setup, runtime, and integrations

**Scope:** `CLAUDE.md`, `tools/_errors.md`, `tools/setup.md`, `tools/integrations/_guide.md`

**Goal of this phase:** All recoverable failures use the same ordered safe-repair flow before the agent says the system is stuck.

- [ ] Turn `tools/_errors.md` into the canonical ordered ladder: probe, inspect logs, retry once, restart transient services, resume the checkpointed install, then escalate.
- [ ] Update `CLAUDE.md` to require that ladder for any recoverable command failure before the agent tells the user a setup/runtime issue is stuck.
- [ ] Update `tools/setup.md` so each failure branch either follows the same ladder or stops at the documented user-consent boundary.
- [ ] Update `tools/integrations/_guide.md` so config-flow failures, OAuth stalls, and stale-flow recovery all reference the same ladder instead of branching to ad hoc instructions.
- [ ] Keep the stop rules explicit: ask before deleting `ha-config`, replacing tokens/accounts, or making a choice inside a config flow or OAuth flow.

**Verification:**

```bash
rg -n "recovery ladder|ha-config|OAuth|config flow|resume the checkpointed install" CLAUDE.md tools/_errors.md tools/setup.md tools/integrations/_guide.md
```

Expected: one shared ladder is referenced everywhere, and there are no conflicting instructions that tell the agent to stop before attempting the safe recovery steps.

## Phase 4: Regression tests for interrupted installs and recovery behavior

**Scope:** `tests/test_install_sh.py`, `tests/test_seed_ha_storage.py`

**Goal of this phase:** The repo proves the exact interrupted-install and recovery cases that failed on OpenClaw are now covered.

- [ ] Add an interrupted-install test in `tests/test_install_sh.py` that simulates seed success, token sync interruption, and a rerun that resumes without browser-token prompting.
- [ ] Add a partial-state test in `tests/test_install_sh.py` that starts with seeded `.storage` plus placeholder or missing `HA_TOKEN` and asserts the installer takes the recovery path instead of proceeding blindly.
- [ ] Extend the install-script tests to assert the phase labels are printed for the slow stages and that a forced failure names the failing phase.
- [ ] Keep `tests/test_seed_ha_storage.py`'s partial-state refusal case, but make the assertion match the new recovery contract so the helper stays strict while `install.sh` owns resume behavior.
- [ ] Add a post-install handoff assertion so the installer output still tells the agent to continue directly into setup after the initial command finishes.

**Verification:**

```bash
python3 -m unittest tests.test_install_sh tests.test_seed_ha_storage -v
```

Expected: the new interrupted-install and recovery tests pass, and the existing seed-helper idempotency and partial-state protection tests still pass.

## Coverage Check

- P1 is covered by Phase 1 and validated again by Phase 4.
- P2 is covered by Phase 2 and validated again by Phase 4.
- P3 is covered by Phase 2 and validated again by Phase 4.
- P4 is covered by Phase 3.
- P5 is covered by Phase 4.
- No finding is left without a concrete implementation phase.
