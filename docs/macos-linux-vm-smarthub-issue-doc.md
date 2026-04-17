# SmartHub macOS Linux VM Issue Document

**Date:** 2026-04-17
**Scope:** `install.sh`, `README.md`, `tools/setup.md`, `tools/integrations/_guide.md`, `tools/_errors.md`, current Linux-first install/runtime assumptions on `origin/main`, official Home Assistant macOS VM guidance, and the proposed macOS host wrapper that provisions `Linux VM + SmartHub`
**Analyst:** Codex

## Summary

I reviewed the reverted `origin/main` baseline against the new goal of supporting macOS by provisioning a Linux VM and then running the existing SmartHub install flow inside that guest. The current repo is still Linux-first end to end: the public install entrypoint assumes a direct Linux host, the docs still teach Pi-style URLs and mDNS behavior, and there is no host-side automation for creating or re-entering a Linux VM from macOS. Seven distinct gaps block a trustworthy “one command from macOS” path today: the supported Mac story is undefined, the installer has no host/guest dispatcher, VM provisioning requirements are not encoded, guest re-entry is not factored, Mac-specific prerequisites and stop conditions are missing, docs/skills still teach the wrong browser/network model, and automated coverage does not protect the new contract.

Overall risk is **High** because this is an installer and support-boundary change that is hard to reverse once users start relying on it. A partially provisioned VM, a half-patched OpenClaw config, or ambiguous host-vs-guest instructions would leave users stuck in a state that is harder to debug than the current Linux-only baseline.

## Intent

**Goal:** Support macOS by creating and provisioning a Linux VM on the Mac host, then running the existing SmartHub install inside that Linux guest so the repo keeps a Linux execution model while macOS gets a one-command bootstrap path.

**Priority ranking:** reliable Linux-guest SmartHub behavior > honest macOS support boundary > one-command UX > minimizing code duplication > optional polish

**Decision boundaries:** The agent can redesign the installer flow, add helper scripts, add tests, and rewrite docs/skills to make macOS VM support explicit. The agent should not silently broaden scope to support Home Assistant OS in a VM, native macOS Docker Desktop, or multiple hypervisors without evidence and a documented reason.

**Stop rules:** Pause and ask if reliable unattended Linux guest installation cannot be achieved with the chosen hypervisor tooling, if host-side installation requires irreversible OS-level permissions we cannot detect or recover from cleanly, or if the implementation would force SmartHub to support both Linux-guest and native macOS HA runtimes at the same time.

## Findings

### P1: The supported macOS story is undefined and currently misleading

**Severity:** High
**Category:** Reliability
**Affected components:** `README.md`, `install.sh`, `tools/setup.md`, `tools/integrations/_guide.md`

**Description:** The public repo still reads like a general “macOS / Linux” SmartHub install even though the reverted baseline only has a Linux-first installer and Pi-style operator guidance. It does not say that the intended Mac story is now `Linux VM + SmartHub`, that the VM exists only while the Mac stays on the home LAN, or that `install.sh` should ultimately run inside the Linux guest.

**Impact:** Mac users will keep trying to run the current Linux-first flow directly on the host, then hit mismatched Docker, network, and setup assumptions before there is any explicit redirect to the VM path.

**Success criteria:**
- [ ] `README.md` defines macOS support as `Linux VM + SmartHub`, not native macOS Home Assistant runtime support.
- [ ] `tools/setup.md` and `tools/integrations/_guide.md` state clearly when the user is on the macOS host versus inside the Linux VM.
- [ ] The public install instructions no longer imply that SmartHub itself runs directly on the macOS host.

---

### P2: `install.sh` has no host-versus-guest dispatcher

**Severity:** High
**Category:** Reliability
**Affected components:** `install.sh`

**Description:** The current installer assumes one direct execution environment: a local machine that already looks like the SmartHub runtime target. It has no Darwin branch, no VM bootstrap entrypoint, no guest handoff, and no explicit detection of whether it is running on the macOS host or inside the provisioned Linux guest.

**Impact:** A single-command macOS experience is impossible because the installer cannot change behavior based on host OS and cannot re-enter itself safely inside the guest after VM provisioning.

**Success criteria:**
- [ ] Running `bash install.sh` on macOS takes the host-bootstrap path instead of trying the Linux install path directly.
- [ ] Running `bash install.sh` inside the Linux VM takes the guest install path and does not attempt to provision another VM.
- [ ] The dispatcher logic has an automated test proving the macOS host path and Linux guest path diverge correctly.

---

### P3: VM provisioning requirements are not encoded anywhere in the product

**Severity:** High
**Category:** Reliability
**Affected components:** `install.sh`, new VM helper scripts, docs

**Description:** The product does not encode the chosen hypervisor workflow: architecture-aware guest image selection, minimum CPU/RAM sizing, EFI, disk creation, network adapter layout, guest SSH reachability, or deterministic unattended guest installation. The repo also does not define how the installer should find and talk to the guest after first boot.

**Impact:** Even if a macOS wrapper is added, users will still be left with manual, inconsistent VM creation steps, which defeats the “one command” goal and makes failures non-reproducible.

**Success criteria:**
- [ ] The chosen VM provisioning path is encoded in code, not just prose, including architecture-sensitive asset selection and minimum VM settings.
- [ ] Where the official Home Assistant macOS VM guidance is still applicable to a Linux guest bootstrap, the automated VM settings match it explicitly: at least `2 GB RAM`, `2 vCPU`, `EFI`, and bridged networking.
- [ ] The host bootstrap can deterministically reach the guest after first boot without asking the user to discover the guest IP manually.
- [ ] Failure messages identify which provisioning step failed and what the user must fix before retrying.

---

### P4: The Linux guest install contract is not factored for re-entry

**Severity:** High
**Category:** Maintainability
**Affected components:** `install.sh`, OpenClaw config patching logic, repo sync logic

**Description:** The current installer interleaves repo sync, OpenClaw config patching, HA seeding, and setup handoff in one linear Linux-first script. There is no explicit “guest install” contract that can be invoked after a macOS host wrapper brings up the VM.

**Impact:** The macOS wrapper would either duplicate half the Linux installer or call back into a script that is not safe to resume/re-enter, increasing drift and making future fixes risky.

**Success criteria:**
- [ ] The Linux-side SmartHub install logic is callable as a distinct guest phase without requiring the macOS host bootstrap context.
- [ ] Re-running the guest install after partial completion is idempotent and does not re-create host-side VM resources.
- [ ] Tests cover at least one resume/re-entry scenario for the guest phase.

---

### P5: macOS host prerequisites, permissions, and stop conditions are not modeled

**Severity:** High
**Category:** Reliability
**Affected components:** `install.sh`, new VM helper scripts, docs

**Description:** A macOS host bootstrap will depend on host-side prerequisites that the current repo does not model: hypervisor installation, command-line tooling availability, host architecture detection, permission prompts, and the possibility that hypervisor installation succeeds only partially. None of these have explicit stop rules or recovery guidance.

**Impact:** The installer may patch OpenClaw, clone the repo, or create partial VM state before the user discovers that the hypervisor is unavailable or blocked by host permissions.

**Success criteria:**
- [ ] The host bootstrap checks prerequisites before mutating repo or OpenClaw state.
- [ ] The installer stops with explicit host-side guidance when the chosen hypervisor cannot be installed or used.
- [ ] Recovery docs explain how to retry after a partial macOS host bootstrap without deleting unrelated SmartHub state.

---

### P6: Docs and skills still teach Linux/Pi networking and browser assumptions

**Severity:** Medium
**Category:** Reliability
**Affected components:** `README.md`, `tools/setup.md`, `tools/_common.md`, `tools/integrations/_guide.md`, `tools/_errors.md`

**Description:** The current documentation and operator skills still assume Pi/Linux behavior: `homeassistant.local`, `hostname -I`, Avahi/systemd helpers, and user-facing links that presume the browser is talking directly to the Linux host. There is no documented distinction between the macOS host bootstrap stage and the Linux guest runtime stage.

**Impact:** Even if the VM bootstrap works, OpenClaw and users will keep emitting the wrong commands on the Mac host or the wrong browser URL on the guest side, especially during onboarding and OAuth/integration flows.

**Success criteria:**
- [ ] Host-side macOS instructions do not use Pi-only commands such as `hostname -I`, `systemctl --user`, or Avahi guidance.
- [ ] Guest-side Linux instructions keep the existing Linux behavior where appropriate, including `homeassistant.local` guidance.
- [ ] Integration/OAuth guidance tells the operator whether a command belongs on the macOS host, the Linux guest, or the browser machine.

---

### P7: Automated coverage does not protect the new macOS host bootstrap contract

**Severity:** Medium
**Category:** Testability
**Affected components:** `tests/test_install_sh.py`, new host-bootstrap tests, doc tests

**Description:** The current automated checks only protect the Linux-first installer and the existing doc contracts on `origin/main`. There is no coverage for Darwin dispatch, VM resource/config command generation, guest handoff, or the rewritten documentation that must distinguish host bootstrap from guest runtime.

**Impact:** The repo could regress the macOS host path or drift back into ambiguous docs without any test failure before release.

**Success criteria:**
- [ ] Installer tests cover macOS host detection and at least one successful handoff into the Linux guest path.
- [ ] Doc tests assert that macOS support is described as `Linux VM + SmartHub` and that `Home Assistant OS in a VM` remains a separate HA-only alternative.
- [ ] Tests fail if host-only instructions leak Linux guest commands or vice versa.

## Accepted Residual Risks

- Hypervisor installation on macOS may still require user-approved OS prompts. The product can automate detection and sequencing, but not guarantee zero user interaction at the OS permission layer.

## Dependencies Between Findings

- P2 depends on P1 because the dispatcher cannot be implemented safely until the supported macOS story is explicit.
- P3 and P5 both feed P2: the host bootstrap needs defined VM requirements and explicit prerequisite handling.
- P4 depends on P2 because guest re-entry only matters once the dispatcher exists.
- P6 depends on P1-P4 because the docs must describe the actual host/guest execution model.
- P7 depends on the final architecture chosen for P2-P6.
