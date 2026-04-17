# Xiaomi Home — Integration Reference

## Overview

Xiaomi Home (`xiaomi_home`) connects Xiaomi/Mi ecosystem devices via the Xiaomi cloud. Devices are managed through the Mi Home app and exposed to Home Assistant after OAuth authentication.

**⚠️ This is a custom integration — requires HACS.** It is NOT the same as `xiaomi_miio` (which is built-in). If HACS is not installed, install it first (see CLAUDE.md HACS Setup section).

## Setup

Uses OAuth config flow. See TOOLS.md for the generic config flow process.

**Integration domain:** `xiaomi_home`
**Source:** HACS (custom integration)

**Start the flow:**
```
Tool: ha_config_entries_flow
  handler: "xiaomi_home"
```

## Cloud Regions

China-purchased devices are almost always on `cn`. Wrong region = 0 devices found.

| Region Code | Region |
|-------------|--------|
| `cn` | China mainland |
| `sg` | Singapore |
| `us` | United States |
| `de` | Germany |
| `ru` | Russia |
| `in` | India |

## OAuth Notes

- `native macOS Docker Desktop` should start from the same-machine browser flow. Use `HA_URL` / `smarthub_default_ha_origin` for dashboard links and local setup guidance.
- The Xiaomi flow may still insist on `homeassistant.local` for `oauth_redirect_url`. If that happens on native macOS Docker Desktop, give the user a same-machine hosts file entry so `homeassistant.local` resolves back to the current HA host, then retry the OAuth link.
- Linux / Raspberry Pi / `Linux VM + SmartHub` can use either working mDNS or a hosts entry for the Linux host IP when `homeassistant.local` is required.
- If the user needs Linux-style hardware or network behavior on a Mac, move to `Linux VM + SmartHub` or `Home Assistant OS in a VM` instead of pretending the native path has Raspberry Pi parity.
- A Mac-hosted VM only has local discovery and local-device control while the Mac remains on the home LAN.
- Extract the OAuth URL from the `description_placeholders` field (may be in an HTML `<a href="...">` tag).
- Send the OAuth URL as a markdown hyperlink: `[Authorize Xiaomi](url)` — see CLAUDE.md for the mandatory URL formatting rule.
- You cannot complete the browser login yourself — the user must open the link and authorize.

## Shared Quirks

- Entity IDs are very long (e.g., `media_player.xiaomi_cn_mitv_3b1ed2f92de5175e4cdf6f66d685ec5c_...`). Always look up the actual entity ID via `ha_search_entities` rather than guessing.
- The Bluetooth integration may enter `setup_retry` state on Linux-hosted installs — the Bluetooth hardware may need a power cycle.
- After setup, devices may take 30-60 seconds to appear in the device registry.

## Devices

| Name | Device File | Type |
|------|-------------|------|
| Xiaomi TV | [tv.md](tv.md) | `media_player` (DLNA) |
| MA8 Air Conditioner | [ma8-ac.md](ma8-ac.md) | `climate` |
| P1V2 Smart Cooker | [p1v2-cooker.md](p1v2-cooker.md) | Smart cooker (rice/multi-cook) |
