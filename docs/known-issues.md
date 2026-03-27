# Known Issues & Notes for Subsequent Development

## 1. OAuth Integrations Require Browser on User's Device

**Problem:** Integrations that use OAuth (e.g., Xiaomi Home, Google, Spotify) redirect to `homeassistant.local` for the callback. If the user's device can't resolve `homeassistant.local`, the OAuth flow fails with `DNS_PROBE_FINISHED_NXDOMAIN`.

**Current workaround:** User must add `192.168.2.97 homeassistant.local` to their OS hosts file (Windows: `C:\Windows\System32\drivers\etc\hosts`). One-time setup.

**Root cause:** The Xiaomi OAuth `redirect_uri` is hardcoded to `http://homeassistant.local:8123/...` by the integration, ignoring HA's `external_url` config.

**Impact on OpenClaw (Phase 2):** When running purely from the Pi, OpenClaw cannot complete OAuth flows on behalf of the user. The user must open a browser and log in.

**Proposed Phase 2 solution:** OpenClaw sends the user a clickable link via the web app chat: "Click here to connect your Xiaomi account" → user clicks → OAuth completes in their browser → OpenClaw detects new devices and confirms in chat. The link generation can use HA's config flow API (`config/config_entries/flow`) to initiate the flow and extract the OAuth URL.

**HA config added to support this:**
```yaml
homeassistant:
  external_url: "http://192.168.2.97:8123"
  internal_url: "http://192.168.2.97:8123"
```

---

## 2. Xiaomi TV DLNA Connection Drops Constantly

**Problem:** Xiaomi TVs have a flaky DLNA (UPnP) implementation. HA subscribes to UPnP events for real-time status, but the TV drops the event subscription after ~10 seconds. HA then marks the entity as `unavailable` even though the TV is reachable on the network.

**Evidence:**
- `ping 192.168.2.110` succeeds (TV is online)
- `curl http://192.168.2.110:49152/description.xml` returns valid DLNA XML
- But `media_player.edgenesis_tv` state = `unavailable` in HA

**Commands still work:** Sending `play_media` via HA API works — the TV plays audio. But the state reverts to `unavailable` immediately after.

**Current workaround in our API:** `api/src/routes/services.ts` auto-reloads the HA config entry for unavailable entities before sending commands (adds ~2s delay per command).

**Better solutions:**
1. **Xiaomi Home integration** (via MIoT cloud) — reliable status and control through Xiaomi's own API. Requires user's Xiaomi account OAuth (see issue #1).
2. **Android TV / ADB integration** — requires enabling Developer Options + Network Debugging on the TV (port 5555). Gives full control: power, volume, apps, remote buttons.
3. **IR blaster (Phase 3)** — Broadlink RM4 Mini sends IR signals for power/volume/input. Works with any TV.

---

## 3. Xiaomi TV Drops Wi-Fi During Standby

**Problem:** The Xiaomi TV disconnects from Wi-Fi when the screen is off / in standby mode. This means HA can't reach it at all until the TV is manually turned on.

**Impact:** No way to send a "wake up" command via network — the device is truly offline.

**Fix (user-side):** TV Settings → Network → "Keep Wi-Fi on during sleep" → Always.

**Fix (with IR blaster, Phase 3):** Send power-on IR signal to wake the TV, then network commands work.

---

## 4. Playwright MCP Not Available on ARM64 (Raspberry Pi)

**Problem:** Playwright's Chromium browser doesn't support Linux ARM64. `npx playwright install` fails with "ERROR: not supported on Linux Arm64".

**Impact:** Cannot use Playwright MCP for browser automation on the Pi.

**Workaround:** Use HA REST/WebSocket APIs directly instead of browser-based automation. All device control and configuration can be done via API calls.

---

## 5. Xiaomi TV Cannot Be Powered On via Network

**Problem:** The Xiaomi TV (edgenesis-tv, `192.168.2.110`, MAC `68:39:43:f7:9d:89`) drops Wi-Fi completely when in standby. No network-based method can wake it:
- Wake-on-LAN: TV has no WoL setting
- ADB: Requires network, which is off in standby
- 米家 (Mi Home) app: TV is not registered as a MIoT device, cannot be controlled via Xiaomi cloud
- DLNA: Network-dependent, doesn't work when TV is off
- Xiaomi Home HA integration (`ha_xiaomi_home`): TV not found — 0 devices in the user's Mi Home family

**What works:** Turn-off works via DLNA when the TV is on. Media casting works. Volume control works (with DLNA config reload workaround).

**Resolution: Phase 3 — IR blaster.** A Broadlink RM4 Mini (~$20) placed near the TV can send the power-on IR signal regardless of network state. This is the standard solution for TVs that drop Wi-Fi in standby.
