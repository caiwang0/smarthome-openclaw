# macOS Docker Desktop Support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver native macOS Docker Desktop support for the mainstream SmartHub flow while preserving the working Linux/Raspberry Pi path, keeping one shared installer/runtime core, and documenting VM fallbacks without substituting them for the native target.

**Architecture:** Split the Home Assistant runtime into one shared Compose base plus narrow per-platform override files, then centralize OS detection and runtime selection in a shared shell helper consumed by `install.sh`, `CLAUDE.md`, and `tools/setup.md`. Keep user-facing platform boundaries in the existing docs, and lock the contract in with install/runtime/doc tests so future changes cannot silently drift the macOS path or regress Linux.

**Tech Stack:** Bash, Docker Compose, Python 3, `unittest`, Markdown docs

**Intent Priority:** successful mainstream macOS setup > preserve the existing Linux/Raspberry Pi behavior > shared installer/runtime core over duplicated scripts > accurate documentation of macOS caveats > implementation convenience

**Issue Doc:** `docs/macos-docker-desktop-issue-doc.md`

**State File:** `docs/macos-docker-desktop-rdw-state.json`

---

## Scope Lock

- Native target remains **SmartHub on macOS through Docker Desktop**.
- `Linux VM + SmartHub` stays documented as a pragmatic workaround for users who need Linux behavior on a Mac today.
- `Home Assistant OS in a VM` stays documented as the official Home Assistant macOS route, not as a substitute for fixing the native SmartHub path.
- No phase may "solve" the problem by redirecting the product to VM-only operation.

## File Map

### Create

| File | Purpose |
|---|---|
| `docker-compose.linux.yml` | Linux-only Home Assistant runtime overrides (`network_mode: host`, Linux host mounts, privileged mode if still required) |
| `docker-compose.macos.yml` | macOS Docker Desktop runtime overrides (published port mapping and any macOS-only settings) |
| `scripts/platform-env.sh` | Shared OS/runtime detection helpers for installer and setup flows |
| `tests/test_platform_env.py` | Unit coverage for shell helper output and platform contract |
| `tests/test_macos_support_docs.py` | Contract tests for README/setup/error doc coverage of native macOS vs VM fallback boundaries |

### Modify

| File | Change Scope |
|---|---|
| `docker-compose.yml` | Reduce to the shared Home Assistant runtime core only |
| `.env.example` | Add any shared runtime variables needed by the override split (for example `HA_PORT`) |
| `install.sh` | Add early OS/tool preflight, shared compose/runtime selection, and cross-platform port/env handling |
| `CLAUDE.md` | Align first-run checks and manual-option links with the new platform helper contract |
| `README.md` | Define the native macOS support target, caveats, and VM fallback boundaries |
| `tools/setup.md` | Use the shared runtime contract, remove unconditional Linux-only setup steps from the macOS path, and surface supported/fallback branches early |
| `tools/_errors.md` | Add platform-specific recovery guidance and native-vs-VM fallback messaging |
| `tools/integrations/_guide.md` | Remove implicit Linux/Pi assumptions from discovery/OAuth guidance and document the macOS-native behavior |
| `tools/integrations/_discovery.md` | Keep discovery read-only while documenting platform caveats where needed |
| `tools/xiaomi-home/_integration.md` | Clarify the macOS OAuth path and when a hosts entry or VM fallback is required |
| `tests/test_install_sh.py` | Add OS detection, preflight, and runtime-selection coverage |
| `tests/test_setup_docs.py` | Assert platform-aware setup flow text and commands |
| `tests/test_integrations_docs.py` | Assert the native macOS / Linux VM / HA OS VM doc contract across integrations |
| `tests/test_recovery_docs.py` | Assert shared recovery/fallback language across setup/integration/error docs |

### No Change

| File | Reason |
|---|---|
| `tools/printer/office-printer.md` | Printer path is unrelated to the macOS Docker Desktop runtime split |
| `tools/automations/_guide.md` | Automation workflow is not part of the macOS runtime/install boundary |
| `ha-config/` | Runtime data volume; do not restructure it in this project |

---

## Phase 1: Runtime Split for Native macOS Support

**Targets:** P1.1, P1.2, P1.3

**Why first:** The issue doc ranks "successful mainstream macOS setup" above everything else. The runtime has to stop assuming a native Linux host before any installer or doc branch can be truthful.

### Task 1.1: Separate shared and platform-specific Compose behavior

**Files:**
- Modify: `docker-compose.yml`
- Create: `docker-compose.linux.yml`
- Create: `docker-compose.macos.yml`
- Modify: `.env.example`

- [ ] Move only shared Home Assistant settings into `docker-compose.yml`: image pin, `./ha-config:/config`, restart policy, and shared environment variables.
- [ ] Move Linux-only runtime assumptions into `docker-compose.linux.yml`: `network_mode: host`, `/etc/localtime`, `/run/dbus`, and `privileged: true` only if validation still shows Linux needs it.
- [ ] Add a macOS override in `docker-compose.macos.yml` that uses published host ports instead of Linux host networking and does not mount Linux-only host paths.
- [ ] Introduce any shared env variables that the split needs in `.env.example` (for example `HA_PORT=8123`), keeping existing Linux defaults working.

**Verification commands:**

```bash
docker compose -f docker-compose.yml -f docker-compose.linux.yml config >/tmp/smarthub-linux-compose.yaml
docker compose -f docker-compose.yml -f docker-compose.macos.yml config >/tmp/smarthub-macos-compose.yaml
grep -n 'network_mode: host' /tmp/smarthub-linux-compose.yaml
grep -n '/run/dbus' /tmp/smarthub-linux-compose.yaml
grep -n 'ports:' /tmp/smarthub-macos-compose.yaml
```

**Expected evidence:**
- Linux render still includes host networking and Linux host mounts.
- macOS render includes published ports and omits Linux-only host mounts.

### Task 1.2: Create one shared platform contract for runtime selection

**Files:**
- Create: `scripts/platform-env.sh`

- [ ] Add `smarthub_detect_platform` that maps `uname -s` to `linux`, `macos`, or `unsupported`.
- [ ] Add `smarthub_compose_files` so the runtime always uses the shared base plus the correct platform override.
- [ ] Add `smarthub_default_ha_origin` so the setup flow can use `http://localhost:${HA_PORT}` on macOS and the Linux-friendly origin on Linux where appropriate.
- [ ] Add a cross-platform port probe helper that does not depend on `ss` being present.

**Verification commands:**

```bash
bash -n scripts/platform-env.sh
python3 -m unittest tests.test_platform_env -v
```

**Expected evidence:**
- Shell helper parses cleanly.
- Tests show `linux` and `macos` both resolve to deterministic compose/origin outputs.

### Task 1.3: Use the shared runtime contract in the operational setup path

**Files:**
- Modify: `CLAUDE.md`
- Modify: `tools/setup.md`

- [ ] Update the first-run and Step 4 commands to source `scripts/platform-env.sh` before calling `docker compose`.
- [ ] Replace unconditional `docker compose up -d` with the helper-selected Compose invocation.
- [ ] Use the platform helper for user-facing Home Assistant URLs so the native macOS path does not default to `homeassistant.local` or Pi-only addressing.
- [ ] Keep the Linux/Raspberry Pi path intact by preserving the Linux-friendly address and runtime behavior on that branch.

**Verification commands:**

```bash
python3 -m unittest tests.test_platform_env tests.test_setup_docs -v
grep -n 'platform-env.sh' CLAUDE.md tools/setup.md
```

**Phase 1 review checkpoint**

- Evidence bundle:
  - Rendered Linux and macOS Compose configs from Task 1.1
  - Passing `tests.test_platform_env`
  - Passing `tests.test_setup_docs`
- Approval bar:
  - Native macOS runtime no longer inherits Linux-only host networking or host mounts.
  - Linux render still preserves the existing Linux/Raspberry Pi runtime contract.
  - `tools/setup.md` and `CLAUDE.md` use the same runtime-selection mechanism.

---

## Phase 2: Installer Preflight and Shared Bootstrap Contract

**Targets:** P2.1, P2.2, P2.3, P2.4, P2.5

**Why second:** Once the runtime contract is real, the installer must surface the correct branch before it mutates the workspace or hands the user into setup.

### Task 2.1: Move platform detection and readiness checks ahead of repo mutation

**Files:**
- Modify: `install.sh`
- Modify: `scripts/platform-env.sh`

- [ ] Detect the host platform before clone/update work and print whether the run is taking the Linux path or the macOS Docker Desktop path.
- [ ] Reject unsupported operating systems before any persistent change.
- [ ] Verify OpenClaw workspace/config presence, `git`, `python3`, `curl`, Docker CLI availability, Docker daemon readiness, and `docker compose` availability before repo sync begins.
- [ ] On macOS, fail early if Docker Desktop is not running or the daemon is unavailable instead of proceeding to clone/patch/bootstrap steps.

**Verification commands:**

```bash
bash -n install.sh
python3 -m unittest tests.test_install_sh.InstallScriptTests.test_install_reports_platform_branch_before_repo_sync -v
python3 -m unittest tests.test_install_sh.InstallScriptTests.test_install_stops_before_clone_when_docker_is_unavailable -v
python3 -m unittest tests.test_install_sh.InstallScriptTests.test_install_stops_before_clone_when_compose_is_missing -v
```

### Task 2.2: Replace Linux-only shell assumptions with cross-platform helpers

**Files:**
- Modify: `install.sh`
- Modify: `scripts/platform-env.sh`
- Modify: `.env.example`

- [ ] Replace the `ss`-only port check with the shared cross-platform helper.
- [ ] Replace BSD-incompatible `sed -i` usage with the existing Python-based file update pattern so macOS shell execution does not fail.
- [ ] Keep Linux host-network conflict handling where still needed, but use the macOS branch to publish a chosen host port rather than rewriting HA internals unnecessarily.
- [ ] Ensure the selected port is written consistently to `.env`/`.env.example` and reflected in the macOS Compose override.

**Verification commands:**

```bash
python3 -m unittest tests.test_install_sh.InstallScriptTests.test_install_uses_cross_platform_env_update_helpers -v
python3 -m unittest tests.test_install_sh.InstallScriptTests.test_install_selects_macos_host_port_without_linux_only_tools -v
python3 -m unittest tests.test_install_sh.InstallScriptTests.test_install_keeps_linux_port_recovery_path_intact -v
```

### Task 2.3: Add actionable failure messages and native-vs-fallback guidance

**Files:**
- Modify: `install.sh`
- Modify: `tools/setup.md`
- Modify: `tools/_errors.md`

- [ ] Add early-failure messages that tell users exactly which prerequisite is missing and which platform branch they are on.
- [ ] When the user’s goal falls outside the native macOS scope, direct them to the documented VM alternatives without claiming the native Docker Desktop target is complete.
- [ ] If OpenClaw is described as helping with the VM path, limit the promise to guidance/partial automation and explicitly leave GUI-only hypervisor steps to the user.

**Verification commands:**

```bash
python3 -m unittest tests.test_install_sh.InstallScriptTests.test_install_emits_macos_fallback_guidance_for_out_of_scope_requirements -v
python3 -m unittest tests.test_setup_docs tests.test_recovery_docs -v
```

### Task 2.4: Keep the setup handoff shared after install completes

**Files:**
- Modify: `install.sh`
- Modify: `tools/setup.md`

- [ ] Keep one installer handoff path into `tools/setup.md`, but make Step 2 onward aware of the selected platform branch.
- [ ] Preserve the existing seeded-token recovery path and Linux behavior while ensuring the macOS branch starts from the correct host URL and runtime command.
- [ ] Make sure install-generated messages do not tell the agent to skip steps that are now platform-specific.

**Verification commands:**

```bash
python3 -m unittest tests.test_install_sh -v
python3 -m unittest tests.test_setup_docs -v
```

**Phase 2 review checkpoint**

- Evidence bundle:
  - Passing targeted install tests for Linux and macOS branches
  - Transcript or captured stdout showing the installer reports the platform branch before repo sync
  - Passing setup/recovery doc tests for the shared handoff
- Approval bar:
  - No workspace mutation happens before platform and Docker readiness checks.
  - macOS errors stop early with actionable next steps.
  - Linux seeded-install recovery still passes its existing tests.

---

## Phase 3: Product Boundary, Setup, Discovery, and OAuth Documentation

**Targets:** P3.1, P3.2, P3.3, P3.4, P3.5, P3.6

**Why third:** The runtime and installer must be real before the docs can truthfully define the support boundary. This phase documents the supported macOS experience without replacing the native target with a VM-only story.

### Task 3.1: Define the native macOS support boundary in the README

**Files:**
- Modify: `README.md`

- [ ] Add a concise support section that defines the native macOS target as the mainstream SmartHub flow through Docker Desktop.
- [ ] Call out constrained feature classes on macOS: Bluetooth, USB radios, and low-level network parity.
- [ ] Distinguish the three Mac stories clearly:
  - native macOS Docker Desktop support
  - `Linux VM + SmartHub` as the pragmatic workaround for running the current repo on a Mac today
  - `Home Assistant OS in a VM` as the official Home Assistant macOS route
- [ ] State that a Mac-hosted VM only has local discovery/control while the Mac remains on the home LAN.

**Verification commands:**

```bash
python3 -m unittest tests.test_macos_support_docs -v
grep -n 'Linux VM + SmartHub' README.md
grep -n 'Home Assistant OS in a VM' README.md
```

### Task 3.2: Make setup and recovery docs platform-aware

**Files:**
- Modify: `tools/setup.md`
- Modify: `tools/_errors.md`
- Modify: `CLAUDE.md`

- [ ] Remove unconditional `apt-get`, `systemctl --user`, `avahi-publish`, `hostname -I`, and `homeassistant.local` assumptions from the native macOS path.
- [ ] Keep Linux/Raspberry Pi instructions on the Linux branch where they are still valid.
- [ ] Document what the setup flow supports before install/add-integration work begins, including when macOS users should stay on the native path versus move to a documented VM path.
- [ ] Align `CLAUDE.md` manual-option links and recovery routing with the updated setup/recovery text.

**Verification commands:**

```bash
python3 -m unittest tests.test_setup_docs tests.test_recovery_docs tests.test_macos_support_docs -v
grep -n 'apt-get' tools/setup.md tools/_errors.md tools/integrations/_guide.md
```

**Expected evidence:**
- Linux-only commands remain only inside Linux-specific branches or fallback guidance.
- macOS path uses native URL/origin language and does not silently depend on Avahi/systemd.

### Task 3.3: Update discovery and integration guidance for the macOS contract

**Files:**
- Modify: `tools/integrations/_guide.md`
- Modify: `tools/integrations/_discovery.md`
- Modify: `tools/xiaomi-home/_integration.md`

- [ ] Keep discovery passive-first and read-only, but remove the assumption that every supported path can run Linux LAN tooling directly.
- [ ] Document when the native macOS path can use same-machine browser flows and when a hosts-file entry or documented VM fallback is needed for integrations that insist on `homeassistant.local`.
- [ ] Keep native macOS as the target in the docs while explicitly labelling `Linux VM + SmartHub` and `Home Assistant OS in a VM` as separate fallback stories.
- [ ] If OpenClaw-guided VM setup is documented, align the fallback instructions to the official macOS guide: correct Intel vs Apple Silicon image, minimum 2 GB RAM, 2 vCPU, EFI, bridged networking, and UTM only as an experienced-user fallback when VirtualBox is unsupported.

**Verification commands:**

```bash
python3 -m unittest tests.test_integrations_docs tests.test_macos_support_docs -v
grep -n 'homeassistant.local' tools/integrations/_guide.md tools/xiaomi-home/_integration.md
```

**Phase 3 review checkpoint**

- Evidence bundle:
  - Passing README/setup/integration/recovery doc tests
  - Human-readable diff showing the three Mac stories are distinct
  - Human-readable diff showing Linux-only instructions are branched, not deleted
- Approval bar:
  - Native macOS Docker Desktop remains the primary documented target.
  - Caveats and fallback paths are explicit but do not replace the native path.
  - Integration/OAuth docs no longer imply Raspberry Pi behavior on macOS.

---

## Phase 4: Regression Coverage for the Linux-vs-macOS Contract

**Targets:** P4.1, P4.2, P4.3

**Why last:** After the runtime, installer, and docs are aligned, the test suite can lock the intended behavior in and prevent future drift.

### Task 4.1: Expand installer coverage for platform detection and preflight

**Files:**
- Modify: `tests/test_install_sh.py`
- Modify: `tests/test_platform_env.py`

- [ ] Add explicit Linux and Darwin test fixtures for `scripts/platform-env.sh`.
- [ ] Add install tests for:
  - platform announcement before repo sync
  - unsupported OS early exit
  - Docker daemon unavailable early exit
  - missing `docker compose` early exit
  - macOS port selection without Linux-only tools
  - Linux recovery path staying intact

**Verification commands:**

```bash
python3 -m unittest tests.test_platform_env tests.test_install_sh -v
```

### Task 4.2: Expand doc contract coverage for setup, recovery, discovery, and VM fallback text

**Files:**
- Create: `tests/test_macos_support_docs.py`
- Modify: `tests/test_setup_docs.py`
- Modify: `tests/test_integrations_docs.py`
- Modify: `tests/test_recovery_docs.py`

- [ ] Assert that the README and setup docs identify native macOS Docker Desktop as the supported target.
- [ ] Assert that Bluetooth/USB/low-level network caveats are documented.
- [ ] Assert that native macOS, `Linux VM + SmartHub`, and `Home Assistant OS in a VM` are all distinguished.
- [ ] Assert that Mac-hosted VM discovery is documented as working only while the Mac remains on the home LAN.
- [ ] Assert that any OpenClaw-assisted VM fallback text matches the official macOS VM guidance values already captured in the issue doc.

**Verification commands:**

```bash
python3 -m unittest tests.test_setup_docs tests.test_integrations_docs tests.test_recovery_docs tests.test_macos_support_docs -v
```

### Task 4.3: Run the full regression suite and capture the locked contract

**Files:**
- No new files beyond the test updates above

- [ ] Run the full Python unittest suite for the repo after all phase changes land.
- [ ] Re-run the Linux and macOS Compose renders so runtime regressions are caught alongside test regressions.
- [ ] Capture the exact commands/results in the phase review summary so Stage 3 reviewers can compare future reruns against the same contract.

**Verification commands:**

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
docker compose -f docker-compose.yml -f docker-compose.linux.yml config >/tmp/smarthub-linux-compose.yaml
docker compose -f docker-compose.yml -f docker-compose.macos.yml config >/tmp/smarthub-macos-compose.yaml
```

**Phase 4 review checkpoint**

- Evidence bundle:
  - Full passing test suite
  - Rendered Linux and macOS Compose configs
  - Short summary of any residual unsupported cases that remain intentionally documented
- Approval bar:
  - Installer tests protect platform detection and preflight.
  - Doc tests protect the native macOS boundary and the Linux-vs-macOS distinction.
  - Runtime config renders still match the intended Linux and macOS contracts.

---

## RDW Stage 3 Execution Notes

- Execute phases strictly in order: 1 → 2 → 3 → 4.
- Do not start Phase 2 until Phase 1 review passes, because the installer must consume the finalized runtime split.
- Do not start Phase 3 until Phase 2 review passes, because the docs must describe the actual installer/runtime behavior, not a draft.
- Do not start Phase 4 until Phase 3 review passes, because the tests should lock the final user-facing contract.
- If any phase reveals that native macOS cannot support a supposedly mainstream flow, stop and escalate with evidence rather than silently broadening the fallback story.

## Traceability Matrix

| Issue Doc Criterion | Planned Coverage | Files | Verification |
|---|---|---|---|
| P1.1 The macOS runtime starts HA without Linux-only host mounts/network semantics | Phase 1 Tasks 1.1-1.3 | `docker-compose.yml`, `docker-compose.macos.yml`, `scripts/platform-env.sh`, `tools/setup.md`, `CLAUDE.md` | Compose renders, `tests.test_platform_env`, `tests.test_setup_docs` |
| P1.2 Linux-only runtime features are explicit instead of silent defaults | Phase 1 Tasks 1.1-1.2 | `docker-compose.linux.yml`, `docker-compose.yml`, `scripts/platform-env.sh` | Compose renders, `tests.test_platform_env` |
| P1.3 Docs/setup distinguish mainstream macOS from Linux-only edge cases | Phase 1 Task 1.3 + Phase 3 Tasks 3.1-3.3 | `README.md`, `tools/setup.md`, `tools/_errors.md`, `tools/integrations/_guide.md`, `tools/xiaomi-home/_integration.md` | `tests.test_setup_docs`, `tests.test_integrations_docs`, `tests.test_macos_support_docs` |
| P2.1 Install flow validates OS and surfaces Linux vs macOS path before bootstrap | Phase 2 Task 2.1 | `install.sh`, `scripts/platform-env.sh` | `tests.test_install_sh` targeted platform/preflight tests |
| P2.2 Install flow checks Docker, daemon, Compose, and OpenClaw readiness before persistent changes | Phase 2 Task 2.1 | `install.sh` | `tests.test_install_sh` early-exit tests |
| P2.3 Platform-specific preflight failures stop early with actionable messages | Phase 2 Tasks 2.1-2.3 | `install.sh`, `tools/_errors.md`, `tools/setup.md` | `tests.test_install_sh`, `tests.test_recovery_docs` |
| P2.4 Native macOS misfit cases point to VM docs without claiming the native target is solved | Phase 2 Task 2.3 + Phase 3 Task 3.1 | `install.sh`, `README.md`, `tools/setup.md`, `tools/_errors.md` | `tests.test_install_sh`, `tests.test_macos_support_docs` |
| P2.5 OpenClaw VM-assist text states what is guided vs still manual and matches the official VM guide | Phase 2 Task 2.3 + Phase 3 Task 3.3 | `README.md`, `tools/setup.md`, `tools/integrations/_guide.md`, `tools/_errors.md` | `tests.test_macos_support_docs`, `tests.test_integrations_docs` |
| P3.1 Repo documents native macOS Docker Desktop as the supported target | Phase 3 Task 3.1 | `README.md` | `tests.test_macos_support_docs` |
| P3.2 Docs call out constrained hardware-adjacent and low-level-network feature classes | Phase 3 Tasks 3.1-3.2 | `README.md`, `tools/setup.md`, `tools/_errors.md` | `tests.test_macos_support_docs`, `tests.test_setup_docs` |
| P3.3 Setup and integration/OAuth guidance tell macOS users what is supported before install/add flow | Phase 3 Tasks 3.2-3.3 | `tools/setup.md`, `tools/integrations/_guide.md`, `CLAUDE.md` | `tests.test_setup_docs`, `tests.test_integrations_docs` |
| P3.4 Docs distinguish native macOS, `Linux VM + SmartHub`, and `Home Assistant OS in a VM` | Phase 3 Tasks 3.1-3.3 | `README.md`, `tools/setup.md`, `tools/_errors.md`, `tools/integrations/_guide.md` | `tests.test_macos_support_docs`, `tests.test_integrations_docs` |
| P3.5 Docs explain that Mac-hosted VM discovery/control only works while the Mac is on the home LAN | Phase 3 Task 3.1 + Task 3.3 | `README.md`, `tools/integrations/_guide.md` | `tests.test_macos_support_docs`, `tests.test_integrations_docs` |
| P3.6 VM fallback steps and OpenClaw guidance align with the official macOS VM instructions | Phase 3 Task 3.3 | `README.md`, `tools/setup.md`, `tools/integrations/_guide.md` | `tests.test_macos_support_docs`, `tests.test_integrations_docs` |
| P4.1 Automated tests cover installer OS detection and platform preflight | Phase 4 Task 4.1 | `tests/test_install_sh.py`, `tests/test_platform_env.py` | `python3 -m unittest tests.test_platform_env tests.test_install_sh -v` |
| P4.2 Automated checks protect the documented Linux-vs-macOS setup and integration/OAuth contract | Phase 4 Task 4.2 | `tests/test_setup_docs.py`, `tests/test_integrations_docs.py`, `tests/test_recovery_docs.py`, `tests/test_macos_support_docs.py` | `python3 -m unittest tests.test_setup_docs tests.test_integrations_docs tests.test_recovery_docs tests.test_macos_support_docs -v` |
| P4.3 Runtime/setup doc changes fail tests when they break the supported macOS boundary or regress Linux | Phase 4 Tasks 4.1-4.3 | all test files above plus Compose renders | Full unittest suite + both Compose config renders |

## Assumptions to Verify During Implementation

- The repo can introduce `HA_PORT` without breaking existing seeded-install flows, as long as `HA_URL` remains the user-facing source of truth.
- A small shared shell helper is preferable to duplicating OS detection logic across `install.sh`, `CLAUDE.md`, and `tools/setup.md`.
- Some integrations may still require a same-machine hosts-file workaround on native macOS if they insist on `homeassistant.local`; if validation disproves that, keep the simpler native path.

## Known Open Risks

- The Xiaomi Home OAuth flow may expose the sharpest native-macOS edge if the upstream integration still insists on `homeassistant.local`; Phase 3 should document the native workaround clearly and escalate only if it blocks the intended mainstream flow.
- Linux-specific runtime flags such as `privileged: true` or `/run/dbus` may turn out to be unnecessary on Linux after the split; if so, remove them in Phase 1 rather than carrying them forward blindly.
- The local environment in this repo does not currently have `rg`; test and verification commands should continue to rely on `python3 -m unittest`, `find`, and `docker compose`.
