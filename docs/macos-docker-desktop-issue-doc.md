# SmartHub macOS Docker Desktop Issue Document

**Date:** 2026-04-17
**Scope:** `docker-compose.yml`, `install.sh`, `README.md`, `tools/setup.md`, `tools/integrations/_guide.md`, `tools/integrations/_discovery.md`, `tools/xiaomi-home/_integration.md`, current SmartHub install/runtime assumptions, macOS VM alternatives, and the macOS Docker Desktop support boundary discussed on 2026-04-17
**Analyst:** Codex

## Summary

I reviewed the current SmartHub install, runtime, and integration flow against the goal of supporting macOS users through Docker Desktop while preserving the mainstream SmartHub experience already working on Raspberry Pi and Linux. The repo is still Linux-first in both runtime topology and setup assumptions, and some of those assumptions continue into user-facing integration and OAuth guidance. Four distinct gaps block a trustworthy macOS path today: Linux-only runtime assumptions are hardcoded, installer preflight is too shallow, the macOS support boundary is undefined, and automated coverage does not protect cross-platform behavior.

The discussion also clarified an important distinction for users: `Linux VM + SmartHub` is the most pragmatic way to run the current repo on a Mac today because it gives SmartHub the Linux environment it already expects, but that is a workaround for users and developers, not proof that native macOS Docker Desktop support is solved. `Home Assistant OS in a VM` is the official Home Assistant macOS route, but it is a different product shape from running the SmartHub repo in a general Linux environment. The official macOS guide currently routes users through a VM hypervisor, with VirtualBox images for Intel and Apple Silicon Macs, at least 2 GB RAM and 2 vCPUs, EFI enabled, and bridged networking so Home Assistant can talk to other devices on the home network; it notes that experienced users can try UTM if VirtualBox is not supported on their Mac.

Overall risk is **High** because macOS users can enter the current setup flow expecting Raspberry Pi-like behavior, but the repo does not currently distinguish between supported mainstream flows and constrained hardware/network edge cases before attempting installation.

## Intent

**Goal:** Support the mainstream SmartHub flow on macOS through Docker Desktop so users can install Home Assistant, connect OpenClaw and `ha-mcp`, complete setup, and use common integrations without weakening the working Linux path, while clearly distinguishing that native target from VM-based workarounds.

**Priority ranking:** successful mainstream macOS setup > preserve the existing Linux/Raspberry Pi behavior > shared installer/runtime core over duplicated scripts > accurate documentation of macOS caveats > implementation convenience

**Decision boundaries:** the agent may define a shared installer with OS detection, platform-specific preflight checks, and a split between portable and Linux-only runtime assumptions; the agent may document caveats for Bluetooth, USB radios, and low-level network parity on macOS; the agent may document `Linux VM + SmartHub` as the pragmatic way to run the current repo on a Mac and `Home Assistant OS in a VM` as the official Home Assistant macOS route; the agent may document or design an OpenClaw-assisted VM setup helper that follows the official macOS VM guidance, including the required hypervisor settings and the limits of GUI-driven setup; the agent may not promise full Raspberry Pi hardware/network parity on macOS Docker Desktop when the host/runtime cannot provide it; the agent may not count Linux VM success as proof that native macOS Docker Desktop support is complete.

**Stop rules:** stop and ask if the requested macOS path changes from "mainstream SmartHub flow with documented caveats" to "full Linux hardware/network parity"; stop and ask if preserving macOS support would require regressing the working Linux/Raspberry Pi path; stop and ask if the design would require a completely separate installer instead of a shared core with platform-specific branching; stop and ask if the requested deliverable changes from "native macOS Docker Desktop support" to "recommend Linux VM or Home Assistant OS VM instead of fixing the native path."

## Findings

### P1: The current Home Assistant container runtime assumes native Linux host behavior

**Severity:** High
**Category:** Runtime Compatibility
**Affected components:** `docker-compose.yml`, `README.md`, `tools/setup.md`

**Description:** The current runtime definition is Linux-shaped. It hardcodes `network_mode: host`, mounts Linux host paths such as `/etc/localtime` and `/run/dbus`, and assumes the host/container relationship behaves like a Raspberry Pi or other Linux machine. Those assumptions are not portable to Docker Desktop on macOS, where host networking is not native Linux host mode and Linux host sockets/paths are not guaranteed to exist in the same way.

**Impact:** A macOS user can follow the existing setup flow and still fail before reaching Home Assistant readiness, or they can complete a partial install while hitting runtime limits that were never surfaced clearly. The product currently treats Linux and macOS as if they are equivalent hosts when they are not.

**Success criteria:**
- [ ] The macOS-supported runtime path can start Home Assistant successfully on Docker Desktop without assuming Linux-only host mounts or native Linux host networking semantics.
- [ ] Linux-only runtime features are explicitly identified instead of being silently required by the default setup path.
- [ ] The docs and setup flow distinguish between the supported mainstream macOS runtime path and Linux-only or hardware-adjacent edge cases.

---

### P2: The installer does not perform environment preflight checks strong enough for cross-platform setup

**Severity:** High
**Category:** Installation
**Affected components:** `install.sh`, `README.md`, `tools/setup.md`

**Description:** The installer checks only a narrow slice of readiness today. It does not fully validate the host OS, Docker installation, Docker daemon readiness, Docker Compose availability, OpenClaw configuration readiness, or platform-specific prerequisites before mutating the workspace and beginning the SmartHub bootstrap path. That is acceptable in a Linux-only mental model but too weak for a cross-platform install experience. It also does not explain when a Mac user is better served by a documented VM workaround because the current repo still expects Linux behavior, nor does it describe whether OpenClaw can guide or partially automate the official macOS VM setup path.

**Impact:** macOS users can enter the install path with missing prerequisites or unsupported Docker Desktop settings and encounter failures later in the flow, after the repo has already been cloned or local state has already been modified. The result is avoidable confusion and a weaker recovery story.

**Success criteria:**
- [ ] The install flow validates host OS and surfaces whether the current run is following the Linux path or the macOS path before starting SmartHub bootstrap work.
- [ ] The install flow checks Docker installation, Docker daemon readiness, Docker Compose availability, and OpenClaw workspace/config readiness before making persistent changes.
- [ ] Platform-specific preflight failures stop early with actionable messages rather than surfacing later as ambiguous runtime errors.
- [ ] When the native macOS path is not a fit for the user's goal, the docs and errors can direct them toward the documented VM alternatives without implying that the native Docker Desktop target is complete.
- [ ] If the repo chooses to assist the VM path, the docs clearly state what OpenClaw can guide automatically versus which hypervisor steps still require user action, and those steps align with the official macOS VM guide.

---

### P3: The macOS support boundary is not documented clearly enough for users to know what is and is not supported

**Severity:** High
**Category:** Product Boundary
**Affected components:** `README.md`, `tools/setup.md`, `tools/_errors.md`, `tools/integrations/_guide.md`, `tools/integrations/_discovery.md`, `tools/xiaomi-home/_integration.md`

**Description:** The current docs present SmartHub as a general install flow across platforms, but they do not define the supported macOS experience in concrete terms. The current conversation established that the intended product boundary for macOS is the mainstream SmartHub flow through Docker Desktop, not guaranteed parity for Bluetooth, USB radio, or low-level network behavior. That boundary is not yet written down anywhere in the repo, including the integration and OAuth guidance that still assumes a Linux or Raspberry Pi host broadcasting `homeassistant.local` on the LAN. The docs also do not explain the difference between three separate Mac stories: native SmartHub support through Docker Desktop, `Linux VM + SmartHub` as the pragmatic way to run the current Linux-first repo on a Mac, and `Home Assistant OS in a VM` as the official Home Assistant macOS route. They also do not capture the current official VM instructions clearly enough for an OpenClaw-guided fallback, such as choosing the correct VirtualBox image for Intel versus Apple Silicon, assigning at least 2 GB RAM and 2 vCPUs, enabling EFI, switching the virtual NIC from NAT to Bridged Adapter, and only suggesting UTM for users already comfortable with virtual machines.

**Impact:** Users can reasonably expect their macOS setup to match a Raspberry Pi host in every detail, or they can choose the wrong Mac setup entirely because the repo does not distinguish Docker Desktop from VM-based alternatives. When reality diverges, the failure appears to be a broken product rather than an unsupported or constrained host/runtime capability. That increases support burden and makes troubleshooting less predictable.

**Success criteria:**
- [ ] The repo documents the supported macOS target as the mainstream SmartHub flow through Docker Desktop.
- [ ] The docs explicitly call out the constrained feature classes on macOS, including hardware-adjacent and low-level networking edge cases, without overstating parity.
- [ ] The setup flow and integration/OAuth guidance tell macOS users what experience is supported before they commit to the install path or an add-integration flow.
- [ ] The docs clearly distinguish native macOS Docker Desktop support from `Linux VM + SmartHub` as a workaround and `Home Assistant OS in a VM` as the official Home Assistant macOS path.
- [ ] The docs explain that a Mac-hosted VM only has local-network discovery and control while that Mac remains on the home LAN.
- [ ] If the repo offers a VM fallback, the documented steps and any OpenClaw guidance align with the official macOS VM instructions instead of inventing a different unsupported path.

---

### P4: Automated coverage does not protect the macOS branch or the Linux-vs-macOS contract

**Severity:** Medium
**Category:** Test Coverage
**Affected components:** `tests/test_install_sh.py`, `tests/test_setup_docs.py`, `tests/test_integrations_docs.py`, `tests/`

**Description:** Current automated checks focus on the Linux-first installer and related setup docs. There is no automated protection for OS detection, macOS preflight behavior, platform-specific runtime selection, or doc assertions covering the supported macOS boundary across setup, discovery, and integration/OAuth guidance. As a result, any future macOS work would be easy to regress without detection.

**Impact:** Even if a macOS path is added, it could silently drift or break while Linux-focused tests continue to pass. That would make cross-platform support fragile and costly to maintain.

**Success criteria:**
- [ ] Automated tests cover installer OS detection and platform-specific preflight behavior.
- [ ] Automated checks protect the documented Linux-vs-macOS setup and integration/OAuth contract.
- [ ] Changes to the runtime or setup docs fail tests when they break the supported macOS boundary or regress the existing Linux path.

## Accepted Residual Risks

- Full Raspberry Pi hardware/network parity is not currently part of the macOS Docker Desktop target.
- Bluetooth-, USB-, and low-level-network-dependent behaviors remain outside the supported mainstream macOS boundary unless later investigation proves they can be supported reliably.
- `Linux VM + SmartHub` is an acceptable workaround for users or developers who need Linux behavior on a Mac today, but it does not satisfy the native macOS Docker Desktop support goal.
- `Home Assistant OS in a VM` remains the official Home Assistant macOS route, but it is not a drop-in replacement for a general Linux VM when the goal is to run the full SmartHub repo, Docker workflow, OpenClaw, and `ha-mcp`.
- A Mac-hosted VM only has LAN discovery and local-device visibility while the Mac itself remains on the home network.
- Even if OpenClaw helps with VM setup, some hypervisor-specific steps may still require direct user interaction in the GUI or macOS permission prompts.

## Dependencies Between Findings

- P1 and P2 are the core blockers. The runtime assumptions and installer assumptions both have to be corrected before a credible macOS path exists.
- P3 depends on P1 and P2 because the documented boundary must reflect the actual runtime and install behavior that the repo supports.
- P4 depends on the resolved P1-P3 contract so the test suite can lock in the intended cross-platform behavior.

## Follow-Up Checklist

- [ ] Define one supported macOS target: mainstream SmartHub flow through Docker Desktop, with caveats for hardware-adjacent and low-level network edge cases.
- [ ] Document the difference between native macOS Docker Desktop support, `Linux VM + SmartHub` as the pragmatic workaround for this repo, and `Home Assistant OS in a VM` as the official Home Assistant route on Mac.
- [ ] If a VM fallback is documented, align it to the current Home Assistant macOS guide: correct Intel versus Apple Silicon image selection, minimum 2 GB RAM and 2 vCPUs, EFI enabled, bridged networking, and UTM only as an experienced-user fallback when VirtualBox is not supported.
- [ ] Add explicit environment preflight checks for OS, Docker installation, Docker readiness, Docker Compose, and OpenClaw readiness before bootstrap begins.
- [ ] Separate portable runtime assumptions from Linux-only runtime assumptions so the macOS path does not inherit unsupported host behavior by default.
- [ ] Update setup and troubleshooting docs to describe the supported macOS flow and the constrained feature classes.
- [ ] Add automated coverage for platform detection, macOS preflight, and the Linux-vs-macOS support contract.
