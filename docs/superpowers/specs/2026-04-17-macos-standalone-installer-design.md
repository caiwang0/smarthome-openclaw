# Design: Temporary Standalone SmartHub Installer Proof for macOS

**Date:** 2026-04-17
**Status:** Proposed
**Author:** Codex

---

## Intent

**Goal:** Add a throwaway standalone installer mode on top of the current macOS Docker Desktop branch so the installer can be run on a Mac without a real OpenClaw installation, while still exercising the Home Assistant bootstrap/runtime logic end-to-end.

**Priority ranking:**
1. Prove the Home Assistant bootstrap path works on macOS from the installer
2. Keep the current Raspberry Pi / OpenClaw installer behavior unchanged by default
3. Keep the standalone diff as small and reversible as possible
4. Avoid duplicating installer logic

**Decision boundaries:**
- The standalone path is temporary and isolated to this branch.
- The default `install.sh` behavior must remain OpenClaw-aware and unchanged.
- Standalone mode may skip only OpenClaw-specific requirements: config lookup, workspace lookup, and `openclaw.json` patching.
- Standalone mode should still run the platform checks, repo sync, `.env` setup, port selection, uv install, HA auth seeding, and final handoff text.

**Stop rules:**
- Stop if enabling standalone mode would regress the default OpenClaw/Raspberry Pi path.
- Stop if the standalone mode requires rewriting large sections of installer logic instead of adding one narrow branch.

---

## Approach

Add an environment-gated installer mode:

```bash
SMARTHUB_STANDALONE=1 bash install.sh
```

In standalone mode:

- The installer clones or updates the repo in `~/Downloads/smarthome-openclaw`
- `CONFIG_FILE` / OpenClaw workspace checks are skipped
- `openclaw.json` patching is skipped
- All Home Assistant bootstrap/runtime steps remain active

Outside standalone mode:

- `install.sh` behaves exactly as it does today

This keeps the proof close to the real installer while avoiding a fake OpenClaw setup on the Mac.

---

## Behavior

### Default mode

No behavior change:

- requires `~/.openclaw/openclaw.json`
- resolves the OpenClaw workspace
- clones into the OpenClaw workspace
- patches `openclaw.json`

### Standalone mode

Behavior changes only where OpenClaw is mandatory:

- target directory becomes `"$HOME/Downloads/smarthome-openclaw"`
- installer skips OpenClaw config/workspace validation
- installer skips the OpenClaw config patch phase
- installer still creates `.env`, selects `HA_PORT`, installs uv, seeds HA auth storage, verifies `.claude/settings.json`, and prints the setup handoff

---

## Testing

### Automated

Add installer tests for:

- standalone mode skips missing OpenClaw config failure
- standalone mode targets `~/Downloads/smarthome-openclaw`
- standalone mode skips the OpenClaw config patch phase
- default mode still requires OpenClaw config

### Manual on macOS

Run:

```bash
SMARTHUB_STANDALONE=1 bash install.sh
```

Expected:

- repo cloned into `~/Downloads/smarthome-openclaw`
- Home Assistant bootstrap files created under `ha-config/.storage`
- `.env` created with `HA_URL=http://localhost:<port>`
- no OpenClaw config error

---

## Risks

- This mode is intentionally not a productized installer path; it is only for Mac proof work on this branch.
- If the diff starts leaking standalone assumptions into the default path, the branch should be discarded instead of merged.
