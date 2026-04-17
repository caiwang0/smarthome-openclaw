---
name: macos-docker-desktop-support-boundary
description: SmartHub macOS support must include integration/OAuth docs and keep native-vs-VM stories distinct.
type: project
---

For SmartHub, "macOS support" does not end at `docker-compose.yml` or `install.sh`. The support boundary has to propagate into discovery, integration, and OAuth docs too, because Linux/Pi assumptions such as `homeassistant.local`, Avahi, and Pi-style LAN behavior otherwise leak back into the user path and undo the native macOS contract.

The three Mac stories must stay separate in future work:

- `native macOS Docker Desktop` is the mainstream SmartHub target.
- `Linux VM + SmartHub` is the pragmatic workaround for running the current repo on a Mac when Linux behavior is required.
- `Home Assistant OS in a VM` is the official Home Assistant macOS route, but it is not the same product shape as running this repo in a Linux VM.

If a VM fallback is documented or automated, it should mirror the official Home Assistant macOS guide rather than inventing a custom path: `VirtualBox`, architecture-matched image (`Intel` vs `Apple Silicon`), at least `2 GB RAM`, `2 vCPUs`, `EFI`, `Bridged Adapter`, and `UTM` only as an experienced-user fallback when VirtualBox is unsupported.

**Source:** RDW workflow `rdw-20260417-macos-docker-desktop`, 2026-04-17
**Why:** Early review rounds failed because the work was initially under-scoped and the VM alternatives were too easy to blur into the native target.
**How to apply:** Any future macOS SmartHub change should check README/install docs and integration/OAuth docs together, and should reject any solution that "passes" by quietly replacing the native target with a VM story.
