# macOS Linux VM + SmartHub Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the repo’s ambiguous macOS story with a supported `Linux VM + SmartHub` path in which `install.sh` bootstraps a Linux VM on the macOS host and then runs the normal SmartHub install inside that Linux guest.

**Architecture:** `install.sh` becomes a dispatcher. On macOS it invokes a dedicated VirtualBox bootstrap helper that installs/checks the hypervisor, provisions a Linux VM with deterministic networking and SSH reachability, then triggers the Linux guest install. On Linux it runs the existing SmartHub install path, refactored into an explicit guest phase. Docs and tests are updated so the host-vs-guest contract is clear and regression protected.

**Tech Stack:** Bash, Python helper snippets, VirtualBox `VBoxManage`, Homebrew cask install for VirtualBox on macOS, Ubuntu Server ISO, unittest-based shell contract tests

---

## File Structure

**Modify**
- `install.sh`
  Dispatcher entrypoint. Detect macOS host vs Linux guest, run prerequisite checks early, then delegate to either the macOS VM bootstrap helper or the Linux guest install path.
- `README.md`
  Reframe macOS support around `Linux VM + SmartHub`; document `Home Assistant OS in a VM` only as a separate HA-only alternative.
- `tools/setup.md`
  Teach OpenClaw how to continue setup inside the Linux guest rather than on the macOS host.
- `tools/integrations/_guide.md`
  Make host-vs-guest command boundaries explicit for dashboard and OAuth flows.
- `tools/_errors.md`
  Add host bootstrap failures, VirtualBox issues, and resume guidance.
- `tests/test_install_sh.py`
  Cover Darwin dispatch, host bootstrap prerequisites, guest re-entry, and resume behavior.
- `tests/test_setup_docs.py`
  Lock the host-vs-guest setup contract.
- `tests/test_integrations_docs.py`
  Lock the integration/OAuth host-vs-guest contract.

**Create**
- `scripts/macos-vm-bootstrap.sh`
  VirtualBox/bootstrap helper for the macOS host. Contains hypervisor install/check logic, VM creation, NIC setup, unattended install orchestration, and SSH handoff.
- `scripts/linux-guest-install.sh`
  Linux guest-only installer body extracted from the current `install.sh`.
- `scripts/macos-vm-env.sh`
  Shared helper for macOS VM defaults and state (VM name, architecture, ISO URL, NIC names, SSH forward port, state file paths).
- `scripts/ubuntu-autoinstall-user-data.yaml`
  Template cloud-init/autoinstall payload for the Ubuntu guest user, SSH server, and first-boot package prerequisites.
- `scripts/ubuntu-autoinstall-meta-data.yaml`
  Minimal companion metadata for unattended install media generation.
- `tests/test_macos_vm_docs.py`
  Doc-contract tests for the new macOS VM story.

**Optional create if needed during implementation**
- `scripts/macos-vm-postinstall.sh`
  First-boot guest postinstall helper if `VBoxManage unattended install` cannot express all required guest setup steps cleanly.

---

## Phase 1: Installer Architecture Split

### Task 1: Add failing tests for host/guest dispatch

**Files:**
- Modify: `tests/test_install_sh.py`
- Modify: `install.sh`

- [ ] **Step 1: Write failing tests for Darwin dispatch and Linux guest re-entry**

Add tests that assert:
- macOS host path exits before OpenClaw workspace mutation if VirtualBox is missing
- Linux guest path does not call macOS bootstrap helpers
- a guest re-entry environment flag prevents recursive VM creation

- [ ] **Step 2: Run the focused installer tests to verify the new cases fail**

Run: `python3 -m unittest tests.test_install_sh -v`
Expected: FAIL on the newly added macOS dispatch / Linux guest re-entry tests.

- [ ] **Step 3: Refactor `install.sh` into explicit dispatcher functions**

Implement this shape:

```bash
main() {
  detect_platform
  case "$PLATFORM" in
    macos) run_macos_vm_bootstrap ;;
    linux) run_linux_guest_install ;;
    *) fail_install "Unsupported host OS" ;;
  esac
}
```

Use an explicit guard such as `SMARTHUB_GUEST_INSTALL=1` or a guest marker file so SSH-driven guest re-entry cannot recurse into the macOS bootstrap path.

- [ ] **Step 4: Re-run the focused installer tests**

Run: `python3 -m unittest tests.test_install_sh -v`
Expected: PASS for the new dispatch tests.

- [ ] **Step 5: Commit**

```bash
git add install.sh tests/test_install_sh.py
git commit -m "refactor: split macOS host dispatch from linux guest install"
```

### Task 2: Extract the Linux guest installer body

**Files:**
- Create: `scripts/linux-guest-install.sh`
- Modify: `install.sh`
- Test: `tests/test_install_sh.py`

- [ ] **Step 1: Write a failing regression test that the Linux path still performs repo sync, config patching, HA seed, and setup handoff**

Extend the installer test harness to assert the extracted guest path still executes the current Linux phases in order.

- [ ] **Step 2: Run the focused installer tests to verify the extraction regression fails**

Run: `python3 -m unittest tests.test_install_sh -v`
Expected: FAIL on the new regression test.

- [ ] **Step 3: Move the current Linux-first install body into `scripts/linux-guest-install.sh`**

Expose a single entrypoint:

```bash
run_linux_guest_install() {
  # existing repo sync, OpenClaw patch, Docker/HA seed, setup handoff
}
```

Have `install.sh` source or invoke it after platform dispatch.

- [ ] **Step 4: Re-run the focused installer tests**

Run: `python3 -m unittest tests.test_install_sh -v`
Expected: PASS with Linux behavior unchanged.

- [ ] **Step 5: Commit**

```bash
git add install.sh scripts/linux-guest-install.sh tests/test_install_sh.py
git commit -m "refactor: extract linux guest installer body"
```

---

## Phase 2: macOS Host Bootstrap with VirtualBox

### Task 3: Encode macOS VM defaults and prerequisite checks

**Files:**
- Create: `scripts/macos-vm-env.sh`
- Create: `scripts/macos-vm-bootstrap.sh`
- Modify: `install.sh`
- Test: `tests/test_install_sh.py`

- [ ] **Step 1: Write failing tests for macOS prerequisite gating**

Cover:
- `uname -s` = `Darwin` chooses the macOS bootstrap helper
- missing `VBoxManage` with missing `brew` fails cleanly before workspace mutation
- missing `VBoxManage` with `brew` available triggers `brew install --cask virtualbox`
- unsupported/unknown macOS arch fails with a clear message

- [ ] **Step 2: Run the focused installer tests to verify these cases fail**

Run: `python3 -m unittest tests.test_install_sh -v`
Expected: FAIL on the new prerequisite tests.

- [ ] **Step 3: Implement `scripts/macos-vm-env.sh`**

Define deterministic values and helpers:

```bash
smarthub_vm_name()            # e.g. smarthub-vm
smarthub_vm_state_dir()       # host-side checkpoint/state
smarthub_vm_arch()            # amd64 or arm64 from uname -m
smarthub_vm_ssh_port()        # fixed host port, e.g. 2222
smarthub_vm_ram_mb()          # minimum 2048
smarthub_vm_cpus()            # minimum 2
smarthub_vm_iso_url()         # architecture-sensitive Ubuntu Server ISO
smarthub_vm_nat_nic()         # for SSH bootstrap
smarthub_vm_bridged_nic()     # for LAN access
```

- [ ] **Step 4: Implement early host prerequisite checks in `scripts/macos-vm-bootstrap.sh`**

Behavior:
- if `VBoxManage` exists, continue
- else if `brew` exists, run `brew install --cask virtualbox`
- else fail with host guidance before mutating OpenClaw or repo state

Stop immediately if macOS install requires manual permission approval and `VBoxManage` is still unavailable after install.

- [ ] **Step 5: Re-run focused installer tests**

Run: `python3 -m unittest tests.test_install_sh -v`
Expected: PASS on the macOS prerequisite cases.

- [ ] **Step 6: Commit**

```bash
git add install.sh scripts/macos-vm-env.sh scripts/macos-vm-bootstrap.sh tests/test_install_sh.py
git commit -m "feat: add macOS VirtualBox prerequisite bootstrap"
```

### Task 4: Create the VirtualBox VM and make it reachable

**Files:**
- Modify: `scripts/macos-vm-bootstrap.sh`
- Create: `scripts/ubuntu-autoinstall-user-data.yaml`
- Create: `scripts/ubuntu-autoinstall-meta-data.yaml`
- Test: `tests/test_install_sh.py`

- [ ] **Step 1: Write failing tests for VM command generation**

Assert the helper generates:
- EFI-enabled VM creation
- `2 GB` RAM and `2` CPUs minimum
- one bridged NIC for LAN
- one NAT NIC with SSH port forwarding
- architecture-aware ISO path/URL usage

- [ ] **Step 2: Run focused installer tests to verify the VM command generation cases fail**

Run: `python3 -m unittest tests.test_install_sh -v`
Expected: FAIL on the new VM command assertions.

- [ ] **Step 3: Implement deterministic VirtualBox VM creation**

Use `VBoxManage` to:
- create/register the VM
- set firmware EFI
- set memory/CPU
- attach storage
- configure NIC1 as bridged
- configure NIC2 as NAT with `--natpf2 "guestssh,tcp,127.0.0.1,<port>,,22"`

Prefer a fixed SSH forwarding port so the host bootstrap never needs to discover the guest IP manually.

- [ ] **Step 4: Implement unattended Ubuntu guest installation**

Use one of these two paths, in this order:
1. `VBoxManage unattended install` with the Ubuntu Server ISO, guest username/password, hostname, and first-boot package/SSH setup
2. If that proves insufficient for the guest packages/SSH contract, generate autoinstall seed files (`user-data`, `meta-data`) and mount them alongside the ISO

The guest must come up with:
- SSH enabled
- `git`, `curl`, and `python3` present
- a known bootstrap user that the host can SSH into

- [ ] **Step 5: Add checkpoint and resume markers**

Store host-side progress in a JSON file under the macOS user’s home, for example:

```json
{
  "vm_name": "smarthub-vm",
  "stage": "vm-created | install-started | ssh-ready | guest-install-triggered"
}
```

This lets retries resume instead of re-creating VM resources blindly.

- [ ] **Step 6: Re-run focused installer tests**

Run: `python3 -m unittest tests.test_install_sh -v`
Expected: PASS on VM command generation and resume tests.

- [ ] **Step 7: Commit**

```bash
git add scripts/macos-vm-bootstrap.sh scripts/ubuntu-autoinstall-user-data.yaml scripts/ubuntu-autoinstall-meta-data.yaml tests/test_install_sh.py
git commit -m "feat: provision Ubuntu VM on macOS via VirtualBox"
```

### Task 5: Trigger the Linux guest install over SSH

**Files:**
- Modify: `scripts/macos-vm-bootstrap.sh`
- Modify: `install.sh`
- Modify: `scripts/linux-guest-install.sh`
- Test: `tests/test_install_sh.py`

- [ ] **Step 1: Write failing tests for guest handoff**

Cover:
- host waits for SSH on the forwarded port
- host clones the SmartHub repo in the guest and invokes `SMARTHUB_GUEST_INSTALL=1 bash install.sh`
- retries do not create a second VM when SSH is already ready

- [ ] **Step 2: Run focused installer tests to verify the handoff cases fail**

Run: `python3 -m unittest tests.test_install_sh -v`
Expected: FAIL on the new SSH handoff tests.

- [ ] **Step 3: Implement guest handoff**

Host helper behavior:

```bash
wait_for_guest_ssh
ssh -p "$VM_SSH_PORT" "$VM_USER@127.0.0.1" \
  "git clone '$REPO_URL' '$GUEST_TARGET' || (cd '$GUEST_TARGET' && git pull --ff-only origin main); cd '$GUEST_TARGET'; SMARTHUB_GUEST_INSTALL=1 bash install.sh"
```

The guest path must skip macOS bootstrap logic and run the Linux install only.

- [ ] **Step 4: Re-run focused installer tests**

Run: `python3 -m unittest tests.test_install_sh -v`
Expected: PASS on guest handoff and non-recursion.

- [ ] **Step 5: Commit**

```bash
git add install.sh scripts/macos-vm-bootstrap.sh scripts/linux-guest-install.sh tests/test_install_sh.py
git commit -m "feat: hand off macOS bootstrap into linux guest install"
```

---

## Phase 3: Docs and Skill Contract Rewrite

### Task 6: Rewrite the public macOS support story

**Files:**
- Modify: `README.md`
- Modify: `tools/setup.md`
- Modify: `tools/_errors.md`
- Test: `tests/test_setup_docs.py`
- Create: `tests/test_macos_vm_docs.py`

- [ ] **Step 1: Write failing doc tests for the VM-only macOS contract**

Assert:
- macOS support is `Linux VM + SmartHub`
- `Home Assistant OS in a VM` is documented only as a separate HA-only alternative
- `install.sh` on macOS is described as a host bootstrap that provisions a Linux VM
- host-only docs do not instruct the user to run Pi-only commands on the Mac

- [ ] **Step 2: Run focused doc tests to verify failure**

Run: `python3 -m unittest tests.test_setup_docs tests.test_macos_vm_docs -v`
Expected: FAIL on the new contract assertions.

- [ ] **Step 3: Rewrite `README.md`, `tools/setup.md`, and `tools/_errors.md`**

Required outcomes:
- Mac support statement becomes VM-only
- setup docs distinguish the macOS host phase from the Linux guest phase
- error docs explain hypervisor install failures, permission prompts, and retry flow

- [ ] **Step 4: Re-run focused doc tests**

Run: `python3 -m unittest tests.test_setup_docs tests.test_macos_vm_docs -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add README.md tools/setup.md tools/_errors.md tests/test_setup_docs.py tests/test_macos_vm_docs.py
git commit -m "docs: reframe macOS support around Linux VM plus SmartHub"
```

### Task 7: Rewrite integration and OAuth guidance for host-vs-guest boundaries

**Files:**
- Modify: `tools/integrations/_guide.md`
- Modify: `tools/_common.md`
- Test: `tests/test_integrations_docs.py`
- Modify: `tests/test_macos_vm_docs.py`

- [ ] **Step 1: Write failing doc tests for host-vs-guest command boundaries**

Assert:
- host-only macOS steps never use `hostname -I`, `systemctl --user`, or Avahi guidance
- guest-side Linux flows keep the current `homeassistant.local`, Avahi, and `hostname -I` guidance only for commands that explicitly run inside the Linux guest
- OAuth/browser guidance says whether a command belongs on the macOS host, Linux guest, or browser machine

- [ ] **Step 2: Run focused doc tests to verify failure**

Run: `python3 -m unittest tests.test_integrations_docs tests.test_macos_vm_docs -v`
Expected: FAIL on the new boundary assertions.

- [ ] **Step 3: Update integration docs**

Required outcomes:
- dashboard links and onboarding instructions clearly reference the Linux guest runtime
- any Mac-specific step is clearly labeled as a host bootstrap step
- the old Docker Desktop and same-machine-hosts-file guidance is removed

- [ ] **Step 4: Re-run focused doc tests**

Run: `python3 -m unittest tests.test_integrations_docs tests.test_macos_vm_docs -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/integrations/_guide.md tools/_common.md tests/test_integrations_docs.py tests/test_macos_vm_docs.py
git commit -m "docs: split macOS host steps from Linux guest integration flow"
```

---

## Phase 4: Final Regression and Validation

### Task 8: Run installer/doc regressions on the new branch

**Files:**
- Modify only if regressions surface during validation

- [ ] **Step 1: Run the installer and doc-focused suite**

Run:

```bash
python3 -m unittest tests.test_install_sh tests.test_setup_docs tests.test_integrations_docs tests.test_macos_vm_docs -v
```

Expected: PASS with all new macOS VM contract tests green.

- [ ] **Step 2: Run the full repo suite**

Run:

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

Expected: PASS with zero failures.

- [ ] **Step 3: Manual contract check**

Verify these strings/behaviors directly:

```bash
grep -n "Linux VM + SmartHub" README.md tools/setup.md tools/_errors.md tools/integrations/_guide.md
grep -n "Home Assistant OS in a VM" README.md tools/integrations/_guide.md
grep -n "VBoxManage\\|brew install --cask virtualbox\\|SMARTHUB_GUEST_INSTALL" install.sh scripts/macos-vm-bootstrap.sh scripts/macos-vm-env.sh scripts/linux-guest-install.sh
```

Expected:
- macOS support language consistently references the VM path
- host bootstrap and guest install files are present
- no leftover “native macOS Docker Desktop” guidance remains in the updated contract files

- [ ] **Step 4: Commit any regression fixes**

```bash
git add -A
git commit -m "test: lock macOS Linux VM install contract"
```

---

## Finding Coverage Matrix

| Finding | Planned coverage |
|---------|------------------|
| P1 | Phase 1 Task 1, Phase 3 Task 6 |
| P2 | Phase 1 Task 1 |
| P3 | Phase 2 Tasks 3-4 |
| P4 | Phase 1 Task 2, Phase 2 Task 5 |
| P5 | Phase 2 Task 3, Phase 3 Task 6 |
| P6 | Phase 3 Tasks 6-7 |
| P7 | Phase 1 Task 1 through Phase 4 Task 8 |

## Review Notes

- The plan intentionally standardizes the first implementation on **VirtualBox only**. Supporting additional hypervisors is deferred unless the implementation proves VirtualBox cannot satisfy the unattended-install and SSH handoff contract.
- The plan intentionally keeps the **runtime target Linux-only**. The macOS host is a bootstrap/provisioning environment, not a Home Assistant runtime target.
- If `VBoxManage unattended install` proves unreliable on current macOS hosts, stop after Phase 2 and escalate rather than silently falling back to manual guest setup.
