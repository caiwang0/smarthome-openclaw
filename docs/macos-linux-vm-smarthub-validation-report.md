# Validation Report — macOS Linux VM + SmartHub

**Date:** 2026-04-17  
**Issue document:** `docs/macos-linux-vm-smarthub-issue-doc.md`  
**Plan document:** `docs/superpowers/plans/2026-04-17-macos-linux-vm-smarthub.md`  
**Total findings:** 7  
**Passed:** 7 | **Failed:** 0 | **Skipped:** 0

## Validation Evidence

Commands run during final validation:

```bash
python3 -m unittest tests.test_install_sh tests.test_setup_docs tests.test_integrations_docs tests.test_macos_vm_docs -v
python3 -m unittest discover -s tests -p 'test_*.py' -v
grep -n "Linux VM + SmartHub" README.md tools/setup.md tools/_errors.md tools/integrations/_guide.md
grep -n "Home Assistant OS in a VM" README.md tools/integrations/_guide.md
grep -n "VBoxManage\\|brew install --cask virtualbox\\|SMARTHUB_GUEST_INSTALL" install.sh scripts/macos-vm-bootstrap.sh scripts/macos-vm-env.sh scripts/linux-guest-install.sh
```

Observed results:

- `python3 -m unittest tests.test_install_sh tests.test_setup_docs tests.test_integrations_docs tests.test_macos_vm_docs -v` → `Ran 18 tests in 9.248s` / `OK`
- `python3 -m unittest discover -s tests -p 'test_*.py' -v` → `Ran 28 tests in 10.845s` / `OK`
- Contract grep output confirmed:
  - `README.md:57` contains `Linux VM + SmartHub`
  - `README.md:65` contains `Home Assistant OS in a VM`
  - `install.sh:74` contains `SMARTHUB_GUEST_INSTALL`
  - `scripts/macos-vm-bootstrap.sh:144` contains `brew install --cask virtualbox`
  - `scripts/macos-vm-bootstrap.sh:223-247` contain the `VBoxManage` VM creation and unattended-install calls

## Results

### P1: The supported macOS story is undefined and currently misleading — PASS

- [x] `README.md` defines macOS support as `Linux VM + SmartHub`, not native macOS HA runtime support.
  Evidence: `README.md:57` says `SmartHub supports macOS through **Linux VM + SmartHub** only.` and `README.md:63` says `Native macOS Docker Desktop is not supported`.
- [x] `tools/setup.md` and `tools/integrations/_guide.md` clearly distinguish `macOS host`, `Linux guest`, and browser roles.
  Evidence: `tools/setup.md` now has a `Host / Guest Boundary` section; `tools/integrations/_guide.md` now has a `Host / Guest Boundary` section; `tests.test_macos_vm_docs` and `tests.test_integrations_docs` both passed.
- [x] Public install instructions no longer imply SmartHub runs directly on the macOS host.
  Evidence: `README.md` now says `install.sh` on the macOS host provisions the Linux VM and reruns inside the guest; `tests.test_macos_vm_docs.MacOSVmDocsTests.test_macos_support_is_vm_only` passed.

### P2: `install.sh` has no host-versus-guest dispatcher — PASS

- [x] Running `bash install.sh` on macOS takes the host-bootstrap path.
  Evidence: `tests.test_install_sh.InstallScriptTests.test_macos_host_path_stops_before_workspace_lookup_without_virtualbox` passed and confirms the Darwin path fails on VirtualBox before any workspace lookup.
- [x] Running `bash install.sh` inside the Linux VM takes the guest install path and does not recurse into host bootstrap.
  Evidence: `install.sh:74` gates on `SMARTHUB_GUEST_INSTALL`; `tests.test_install_sh.InstallScriptTests.test_linux_guest_install_helper_exposes_entrypoint` and the guest-handoff tests passed.
- [x] Dispatcher logic has automated coverage for both paths.
  Evidence: `tests/test_install_sh.py` now includes Darwin prerequisite, VM generation, SSH handoff, and resume cases; `python3 -m unittest tests.test_install_sh -v` passed with 13 tests.

### P3: VM provisioning requirements are not encoded anywhere in the product — PASS

- [x] VM provisioning is encoded in code, including architecture-sensitive asset selection and minimum VM settings.
  Evidence: `scripts/macos-vm-env.sh` defines architecture, ISO URL, RAM, CPU, disk, bridge adapter, and SSH port helpers; `tests.test_install_sh.InstallScriptTests.test_macos_host_path_generates_virtualbox_vm_commands` passed.
- [x] The automated VM settings explicitly match the intended minimums.
  Evidence: the command-generation test confirmed `--firmware efi --memory 2048 --cpus 2`, bridged NIC1, NAT NIC2, and the architecture-sensitive ISO path.
- [x] Host bootstrap reaches the guest without asking the user to discover the guest IP manually.
  Evidence: `scripts/macos-vm-bootstrap.sh` uses fixed port `2222` plus `wait_for_guest_ssh`; `tests.test_install_sh.InstallScriptTests.test_macos_host_path_waits_for_guest_ssh_and_triggers_guest_install` passed.
- [x] Failure messages identify which provisioning step failed and what to fix.
  Evidence: prerequisite tests cover missing VirtualBox / unsupported arch; code paths in `scripts/macos-vm-bootstrap.sh` emit explicit VirtualBox, curl, and SSH recovery guidance.

### P4: The Linux guest install contract is not factored for re-entry — PASS

- [x] Linux-side install logic is callable as a distinct guest phase.
  Evidence: `scripts/linux-guest-install.sh` exposes `run_linux_guest_install`; verified by `tests.test_install_sh.InstallScriptTests.test_linux_guest_install_helper_exposes_entrypoint`.
- [x] Re-running the guest install is idempotent and does not recreate host-side VM resources.
  Evidence: `tests.test_install_sh.InstallScriptTests.test_macos_host_path_resume_skips_vm_creation_when_ssh_ready` passed and proves checkpointed resume skips `VBoxManage createvm`.
- [x] Resume/re-entry is covered by automated tests.
  Evidence: both the checkpoint/token restore tests and the macOS resume test passed in `tests.test_install_sh`.

### P5: macOS host prerequisites, permissions, and stop conditions are not modeled — PASS

- [x] Host bootstrap checks prerequisites before mutating repo or OpenClaw state.
  Evidence: `tests.test_install_sh.InstallScriptTests.test_macos_host_path_stops_before_workspace_lookup_without_virtualbox` passed and proves the host path stops before workspace lookup.
- [x] Installer stops with explicit host guidance when the hypervisor cannot be installed or used.
  Evidence: `tests.test_install_sh.InstallScriptTests.test_macos_host_path_installs_virtualbox_with_brew_when_missing` and `test_macos_host_path_rejects_unknown_arch` both passed.
- [x] Recovery docs explain how to retry after partial macOS host bootstrap.
  Evidence: `tools/_errors.md` now includes a `macOS host bootstrap issues` table and a recovery-ladder step for rerunning `install.sh` on the macOS host.

### P6: Docs and skills still teach Linux/Pi networking and browser assumptions — PASS

- [x] Host-side macOS instructions no longer tell the user to run Pi-only commands on the Mac.
  Evidence: `tools/setup.md` and `tools/integrations/_guide.md` now explicitly say the macOS host must not run Docker, `hostname -I`, `systemctl --user`, or Avahi commands; `tests.test_integrations_docs.IntegrationDocsTests.test_host_guest_browser_boundaries_are_explicit` passed.
- [x] Guest-side Linux instructions keep the Linux-only `homeassistant.local`/mDNS behavior where appropriate.
  Evidence: `tools/setup.md` Step 4b and `tools/integrations/_guide.md` OAuth guidance keep `homeassistant.local`, Avahi, and `hostname -I` inside the Linux guest only.
- [x] Integration/OAuth guidance labels macOS host vs Linux guest vs browser machine.
  Evidence: `tools/integrations/_guide.md` now has explicit `macOS host`, `Linux guest`, and `browser machine` language; `tests.test_integrations_docs.IntegrationDocsTests.test_host_guest_browser_boundaries_are_explicit` passed.

### P7: Automated coverage does not protect the new macOS host bootstrap contract — PASS

- [x] Installer tests cover macOS host detection and successful handoff into the Linux guest path.
  Evidence: `tests/test_install_sh.py` includes prerequisite, VM generation, SSH wait, guest bootstrap, and resume cases; 13 installer tests passed.
- [x] Doc tests assert `Linux VM + SmartHub` support and keep `Home Assistant OS in a VM` separate.
  Evidence: `tests/test_macos_vm_docs.py` passed.
- [x] Tests fail if host-only instructions leak Linux guest commands or vice versa.
  Evidence: `tests.test_integrations_docs.IntegrationDocsTests.test_host_guest_browser_boundaries_are_explicit` passed.

## Accepted Residual Risks

- Hypervisor installation on macOS may still require user-approved OS prompts. The product can detect and sequence those prompts, but it cannot remove the OS approval step itself.

## New Issues Discovered During Implementation

- The first guest-handoff implementation assumed OpenClaw already existed in the Linux guest. This was resolved before final validation by bootstrapping OpenClaw and a default `~/.openclaw/openclaw.json` in the guest before re-entering `install.sh`.

## Verdict

**ALL PASS.** The issue document’s seven findings are covered by implemented code, rewritten docs, and automated validation evidence.
