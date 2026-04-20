# macOS Standalone Installer Proof Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a throwaway standalone mode to `install.sh` that clones into `~/Downloads` and skips only OpenClaw-specific steps so the macOS installer path can be proven without a real OpenClaw install.

**Architecture:** Keep the default installer behavior unchanged. Add a narrow `SMARTHUB_STANDALONE=1` branch inside `install.sh`, cover it with installer tests, and continue to exercise the same HA/bootstrap logic after repo sync.

**Tech Stack:** Bash, Python 3, `unittest`

---

## File Map

- Modify: `install.sh`
- Modify: `tests/test_install_sh.py`

## Task 1: Add failing standalone installer tests

**Files:**
- Modify: `tests/test_install_sh.py`

- [ ] Add a test that runs `install.sh` with `SMARTHUB_STANDALONE=1`, no OpenClaw config, and expects success.
- [ ] Assert the standalone target is `~/Downloads/smarthome-openclaw`.
- [ ] Assert standalone mode skips the OpenClaw config patch phase.
- [ ] Assert default mode still fails when OpenClaw config is missing.

## Task 2: Implement the minimal standalone installer branch

**Files:**
- Modify: `install.sh`

- [ ] Add a standalone-mode flag parser from `SMARTHUB_STANDALONE`.
- [ ] In standalone mode, bypass OpenClaw config/workspace lookup and use `"$HOME/Downloads"` as the clone root.
- [ ] Skip the OpenClaw config patch phase in standalone mode.
- [ ] Keep repo sync, `.env`, port handling, uv, HA auth bootstrap, `.claude/settings.json` verification, and handoff logic unchanged.

## Task 3: Verify

**Files:**
- Modify: `tests/test_install_sh.py`
- Modify: `install.sh`

- [ ] Run `python3 -m unittest tests.test_install_sh -v`.
- [ ] Run the full suite: `python3 -m unittest discover -s tests -p 'test_*.py' -v`.
- [ ] Summarize the exact Mac command sequence for the user: `SMARTHUB_STANDALONE=1 bash install.sh`, expected target path, and follow-up checks.
