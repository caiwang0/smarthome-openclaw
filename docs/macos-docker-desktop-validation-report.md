# Validation Report

**Date:** 2026-04-17
**Issue document:** `docs/macos-docker-desktop-issue-doc.md`
**Workflow state:** `docs/macos-docker-desktop-rdw-state.json`
**Total findings:** 4
**Passed:** 4 | **Failed:** 0 | **Skipped:** 0

**Validation note:** This workspace is Linux, so native macOS Docker Desktop runtime behavior was validated from the repo contract that can be exercised here: Compose renders, platform-aware helper tests, installer tests, and doc-contract tests. No live macOS host was available for an end-to-end Docker Desktop run.

## Results

### P1: The current Home Assistant container runtime assumes native Linux host behavior — PASS

- [x] The macOS-supported runtime path can start Home Assistant successfully on Docker Desktop without assuming Linux-only host mounts or native Linux host networking semantics.
  Evidence:
  - Ran `docker compose -f docker-compose.yml -f docker-compose.linux.yml config >/tmp/smarthub-linux-compose.yaml && docker compose -f docker-compose.yml -f docker-compose.macos.yml config >/tmp/smarthub-macos-compose.yaml && grep -n 'network_mode: host\|/run/dbus' /tmp/smarthub-linux-compose.yaml && grep -n 'ports:' /tmp/smarthub-macos-compose.yaml`
  - Output showed Linux-only runtime assumptions only in the Linux render:
    - `linux`
    - `7:    network_mode: host`
    - `21:        source: /run/dbus`
    - `22:        target: /run/dbus`
    - `macos`
    - `9:    ports:`
  Verdict: PASS for the repo/runtime contract; the macOS override omits Linux-only mounts/network semantics and publishes host ports instead.

- [x] Linux-only runtime features are explicitly identified instead of being silently required by the default setup path.
  Evidence:
  - Same Compose render output as above.
  - Ran `python3 -m unittest tests.test_platform_env tests.test_install_sh -v`
  - Output: `Ran 17 tests in 38.333s` / `OK`
  Verdict: PASS; `scripts/platform-env.sh` and the split compose files make Linux-vs-macOS runtime selection explicit and tested.

- [x] The docs and setup flow distinguish between the supported mainstream macOS runtime path and Linux-only or hardware-adjacent edge cases.
  Evidence:
  - Ran `python3 -m unittest tests.test_setup_docs tests.test_integrations_docs tests.test_recovery_docs tests.test_macos_support_docs -v`
  - Output: `Ran 8 tests in 0.004s` / `OK`
  - Ran `grep -nE 'Native macOS Docker Desktop|Bluetooth|USB radios|low-level networking|Linux VM \\+ SmartHub|Home Assistant OS in a VM' README.md tools/setup.md tools/_errors.md`
  - Output included:
    - `README.md:67:**Native macOS Docker Desktop** is the supported Mac target...`
    - `README.md:73:- Bluetooth`
    - `README.md:74:- USB radios`
    - `README.md:75:- low-level networking`
    - `tools/setup.md:65:> Native macOS support covers the mainstream SmartHub flow only...`
  Verdict: PASS.

### P2: The installer does not perform environment preflight checks strong enough for cross-platform setup — PASS

- [x] The install flow validates host OS and surfaces whether the current run is following the Linux path or the macOS path before starting SmartHub bootstrap work.
- [x] The install flow checks Docker installation, Docker daemon readiness, Docker Compose availability, and OpenClaw workspace/config readiness before making persistent changes.
- [x] Platform-specific preflight failures stop early with actionable messages rather than surfacing later as ambiguous runtime errors.
- [x] When the native macOS path is not a fit for the user's goal, the docs and errors can direct them toward the documented VM alternatives without implying that the native Docker Desktop target is complete.
- [x] If the repo chooses to assist the VM path, the docs clearly state what OpenClaw can guide automatically versus which hypervisor steps still require user action, and those steps align with the official macOS VM guide.
  Evidence:
  - Ran `python3 -m unittest tests.test_platform_env tests.test_install_sh -v`
  - Output: `Ran 17 tests in 38.333s` / `OK`
  - The passing installer suite includes:
    - `test_install_reports_platform_branch_before_repo_sync`
    - `test_install_stops_before_clone_when_docker_is_unavailable`
    - `test_install_stops_before_clone_when_compose_is_missing`
    - `test_install_stops_before_clone_when_docker_desktop_is_not_running`
    - `test_install_selects_macos_host_port_without_linux_only_tools`
    - `test_install_keeps_linux_port_recovery_path_intact`
    - `test_install_emits_macos_fallback_guidance_for_out_of_scope_requirements`
  Verdict: PASS.

### P3: The macOS support boundary is not documented clearly enough for users to know what is and is not supported — PASS

- [x] The repo documents the supported macOS target as the mainstream SmartHub flow through Docker Desktop.
- [x] The docs explicitly call out the constrained feature classes on macOS, including hardware-adjacent and low-level networking edge cases, without overstating parity.
- [x] The setup flow and integration/OAuth guidance tell macOS users what experience is supported before they commit to the install path or an add-integration flow.
- [x] The docs clearly distinguish native macOS Docker Desktop support from `Linux VM + SmartHub` as a workaround and `Home Assistant OS in a VM` as the official Home Assistant macOS path.
- [x] The docs explain that a Mac-hosted VM only has local-network discovery and control while that Mac remains on the home LAN.
- [x] If the repo offers a VM fallback, the documented steps and any OpenClaw guidance align with the official macOS VM instructions instead of inventing a different unsupported path.
  Evidence:
  - Ran `python3 -m unittest tests.test_setup_docs tests.test_integrations_docs tests.test_recovery_docs tests.test_macos_support_docs -v`
  - Output: `Ran 8 tests in 0.004s` / `OK`
  - Ran `grep -nE 'Native macOS Docker Desktop|Linux VM \\+ SmartHub|Home Assistant OS in a VM|Bridged Adapter|while the Mac remains on the home LAN' README.md tools/setup.md tools/_errors.md`
  - Output included:
    - `README.md:67:**Native macOS Docker Desktop** is the supported Mac target...`
    - `README.md:79:- \`Linux VM + SmartHub\` is the pragmatic workaround...`
    - `README.md:80:- \`Home Assistant OS in a VM\` is the official Home Assistant macOS route...`
    - `README.md:82:A Mac-hosted VM only has local discovery and local-device control **while the Mac remains on the home LAN**.`
    - `README.md:84:... assign at least \`2 GB RAM\` and \`2 vCPUs\`, enable \`EFI\`, switch networking to \`Bridged Adapter\`...`
  - Ran `grep -nE 'smarthub_default_ha_origin|same-machine browser flow|If an integration insists on \`homeassistant.local\`|hosts file entry|VirtualBox|Apple Silicon|2 GB RAM|2 vCPUs|EFI|Bridged Adapter|UTM' tools/integrations/_guide.md tools/xiaomi-home/_integration.md tools/integrations/_discovery.md CLAUDE.md`
  - Output included:
    - `tools/integrations/_guide.md:15:- \`native macOS Docker Desktop\` is the primary Mac path. Use the same-machine browser flow from \`smarthub_default_ha_origin\`.`
    - `tools/integrations/_guide.md:227:- **If an integration insists on \`homeassistant.local\`**, branch explicitly...`
    - `tools/integrations/_guide.md:231:... \`VirtualBox\` ... \`Apple Silicon\` ... \`2 GB RAM\` ... \`2 vCPUs\` ... \`EFI\` ... \`Bridged Adapter\` ... \`UTM\` ...`
    - `tools/xiaomi-home/_integration.md:37:- \`native macOS Docker Desktop\` should start from the same-machine browser flow...`
  Verdict: PASS.

### P4: Automated coverage does not protect the macOS branch or the Linux-vs-macOS contract — PASS

- [x] Automated tests cover installer OS detection and platform-specific preflight behavior.
- [x] Automated checks protect the documented Linux-vs-macOS setup and integration/OAuth contract.
- [x] Changes to the runtime or setup docs fail tests when they break the supported macOS boundary or regress the existing Linux path.
  Evidence:
  - Ran `python3 -m unittest tests.test_platform_env tests.test_install_sh -v`
  - Output: `Ran 17 tests in 38.333s` / `OK`
  - Ran `python3 -m unittest tests.test_setup_docs tests.test_integrations_docs tests.test_recovery_docs tests.test_macos_support_docs -v`
  - Output: `Ran 8 tests in 0.004s` / `OK`
  - Ran `python3 -m unittest discover -s tests -p 'test_*.py' -v`
  - Output: `Ran 34 tests in 39.955s` / `OK`
  Verdict: PASS.

## Accepted Residual Risks

- Full Raspberry Pi hardware/network parity is still outside the native macOS Docker Desktop target.
- Bluetooth-, USB-, and low-level-network-dependent behaviors remain outside the supported mainstream macOS boundary unless later investigation proves they can be supported reliably.
- `Linux VM + SmartHub` remains a user/developer workaround, not proof that native macOS Docker Desktop support is finished.
- `Home Assistant OS in a VM` remains the official Home Assistant macOS route, but it is not a drop-in replacement for a general Linux VM when the goal is to run the full SmartHub repo.
- A Mac-hosted VM only has LAN discovery and local-device visibility while the Mac itself remains on the home network.
- Some hypervisor-specific steps may still require GUI interaction or macOS permission prompts even when OpenClaw assists the VM fallback.

## New Issues Discovered

None.

## Verdict

All 4 findings validate cleanly against the issue document, with the native macOS runtime verdict explicitly limited to the repo/runtime contract that can be exercised from this Linux workspace.
