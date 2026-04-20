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

- The `oauth_redirect_url` MUST be `http://homeassistant.local:8123` — the integration enforces this.
- Users need `homeassistant.local` in their hosts file pointing to the Linux host's IP address, or mDNS must be running. Run `hostname -I | awk '{print $1}'` to find the IP.
- Extract the OAuth URL from the `description_placeholders` field (may be in an HTML `<a href="...">` tag).
- Send the OAuth URL as a markdown hyperlink: `[Authorize Xiaomi](url)` — see CLAUDE.md for the mandatory URL formatting rule.
- You cannot complete the browser login yourself — the user must open the link and authorize.

## Shared Quirks

- Entity IDs are very long (e.g., `media_player.xiaomi_cn_mitv_3b1ed2f92de5175e4cdf6f66d685ec5c_...`). Always look up the actual entity ID via `ha_search_entities` rather than guessing.
- The Bluetooth integration may enter `setup_retry` state — the Linux host's Bluetooth hardware may need a power cycle.
- After setup, devices may take 30-60 seconds to appear in the device registry.

## Devices

| Name | Device File | Type |
|------|-------------|------|
| Xiaomi TV | [tv.md](tv.md) | `media_player` (DLNA) |
| MA8 Air Conditioner | [ma8-ac.md](ma8-ac.md) | `climate` |
| P1V2 Smart Cooker | [p1v2-cooker.md](p1v2-cooker.md) | Smart cooker (rice/multi-cook) |
