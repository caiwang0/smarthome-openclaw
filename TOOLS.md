# TOOLS.md - Smart Home Setup

## SmartHub API (convenience layer)

The SmartHub API runs at `http://localhost:3099` and wraps Home Assistant.

### List all devices
```bash
curl -s http://localhost:3099/api/devices | jq '.devices[] | {name, device_type, status, area_name, primary_entity}'
```

### Get a specific device
```bash
curl -s http://localhost:3099/api/devices/<device_id>
```

### Control a device (call a service)
```bash
curl -s -X POST http://localhost:3099/api/services/<domain>/<service> \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "<entity_id>"}'
```

Common services:
- `light/turn_on` — turn on a light (optional: `"brightness": 0-255`)
- `light/turn_off` — turn off a light
- `switch/turn_on` / `switch/turn_off` — toggle a switch
- `climate/set_temperature` — set thermostat (data: `"temperature": 24`)
- `climate/set_hvac_mode` — set mode (data: `"hvac_mode": "cool"`)
- `media_player/turn_off` — turn off media player
- `media_player/volume_up` / `media_player/volume_down`
- `media_player/media_play` / `media_player/media_pause`

### List areas/rooms
```bash
curl -s http://localhost:3099/api/areas | jq '.areas'
```

---

## Home Assistant Direct API (for operations not in SmartHub)

When the SmartHub API doesn't expose an endpoint you need, call HA directly at `http://localhost:8123`.

**Authentication header (required for all HA calls):**
```bash
HA_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJkMDYzMDM3YzZiMTI0MGYyOTM2MmZmNGI1ZDA2ZDE1ZCIsImlhdCI6MTc3NDUxMTEwNiwiZXhwIjoyMDg5ODcxMTA2fQ.MMWtEXXmGNE5p_mqdn-RfLD-6j77ntZgc7r9hAvENjo"
```

### Device registry — move device to area
```bash
curl -s -X POST http://localhost:8123/api/config/device_registry \
  -H "Authorization: Bearer $HA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"device_id": "<device_id>", "area_id": "<area_id>"}'
```

### Area registry — create/list/delete areas
```bash
# List areas
curl -s http://localhost:8123/api/config/area_registry/list \
  -H "Authorization: Bearer $HA_TOKEN"

# Create area
curl -s -X POST http://localhost:8123/api/config/area_registry/create \
  -H "Authorization: Bearer $HA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Office"}'

# Delete area
curl -s -X POST http://localhost:8123/api/config/area_registry/delete \
  -H "Authorization: Bearer $HA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"area_id": "<area_id>"}'
```

### Config entries — list installed integrations
```bash
curl -s http://localhost:8123/api/config/config_entries/entry \
  -H "Authorization: Bearer $HA_TOKEN" | jq '.[] | {domain, title, state}'
```

### Config flows — add new integrations

**When a user wants to add an integration, ALWAYS start your response with both options:**

> **Option 1 — Do it yourself in the HA UI:** [Open HA Integrations](http://192.168.2.97:8123/config/integrations/dashboard) → click "Add Integration" → search for [integration name]. Let me know when you're done and I'll check what devices were added.
>
> **Option 2 — I'll guide you step by step.** Here's the first step:

Then immediately show the first form step below. This way the user sees both options at once and can pick either without waiting.

**For guided setup:**

Every integration has different steps and options. NEVER hardcode or assume values. Read the actual `data_schema` from each step and present ALL options to the user.

**Step 1: Start a config flow**
```bash
curl -s -X POST http://localhost:8123/api/config/config_entries/flow \
  -H "Authorization: Bearer $HA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"handler": "<integration_domain>"}'
```

**Step 2: For EVERY step, read the response and act based on `type`:**

| `type` | Action |
|--------|--------|
| `form` | Read `data_schema`, present ALL fields to user, ask for their choices, then submit |
| `external` / `progress` | Extract OAuth URL, send to user as clickable link, wait for them to confirm |
| `abort` | Tell user the reason. If `already_in_progress`, offer to clear stale flows |
| `create_entry` | Done! Show what devices were added |

**For `form` steps — present every field:**
- `select` → show all options as a numbered list, ask user to pick
- `multi_select` → show all options, ask user to pick one or more
- `boolean` → ask yes/no, show the default
- `string` / `integer` → ask user to type a value
- **NEVER auto-fill fields without asking the user**, even if there's a default

**For OAuth steps:**
- Extract the raw URL from the response (may be in `description_placeholders` as an HTML `<a href="...">` tag — extract the `href` value)
- **Send the raw URL on its own line** so Discord auto-links it. Do NOT use markdown `[text](url)` format — Discord doesn't render those as clickable in bot messages. Just paste the URL directly.
- Tell user: "Click the link, log in, authorize, and let me know when done."
- If `homeassistant.local` doesn't load, tell them to add a hosts entry: `192.168.2.97 homeassistant.local`
- After user confirms, poll the flow to check if it advanced

**Step 3: Submit user's choices**
```bash
curl -s -X POST http://localhost:8123/api/config/config_entries/flow/<flow_id> \
  -H "Authorization: Bearer $HA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"field_name": "user_choice", ...}'
```

**Step 4: Repeat until `type` = `create_entry`**

**Clearing stale flows (if `already_in_progress`):**
```bash
curl -s -X DELETE http://localhost:8123/api/config/config_entries/flow/<flow_id> \
  -H "Authorization: Bearer $HA_TOKEN"
```

### Config entries — remove an integration
```bash
curl -s -X DELETE http://localhost:8123/api/config/config_entries/entry/<entry_id> \
  -H "Authorization: Bearer $HA_TOKEN"
```

### Config entries — reload an integration
```bash
curl -s -X POST http://localhost:8123/api/config/config_entries/entry/<entry_id>/reload \
  -H "Authorization: Bearer $HA_TOKEN"
```

---

## Known Devices

| Name | Device ID | Type |
|------|-----------|------|
| 小米 Xiaomi TV | `edgenesis-tv` | `xiaomi.tv.v1` |

## Known Issues
- Xiaomi TV (DLNA) frequently shows as "unavailable" but still accepts commands. Try the command anyway.
- TV cannot be powered on via network when in standby (Wi-Fi disconnects). Requires IR blaster (Phase 3).
- OAuth integrations (Xiaomi Home) require the user to open a URL in their browser — you cannot complete the browser login yourself. The redirect URI uses `homeassistant.local` which resolves via mDNS. If the user's device can't resolve it, guide them to add a hosts entry for `192.168.2.97 homeassistant.local`. **Never modify the OAuth URL itself — Xiaomi rejects mismatched redirect URIs.**
- The Bluetooth integration is in `setup_retry` state — the Pi's Bluetooth hardware may need a power cycle.

## Printing

**Printer:** Network printer at `ipp://192.168.2.75:631/ipp/print` (90% toner)

**Setup (one-time):** CUPS must be installed and the printer added before printing works.
```bash
sudo apt-get install -y cups
sudo lpadmin -p office-printer -E -v ipp://192.168.2.75:631/ipp/print -m everywhere
sudo lpoptions -d office-printer
```

**Printing a file:** When the user uploads a file and says "print this":
1. Save the uploaded file to `/tmp/`
2. Run: `lp -d office-printer /tmp/<filename>`
3. Confirm the print job was sent

If CUPS isn't running: `sudo systemctl start cups`

If the printer isn't added yet, run the setup commands above first.

---

## Network Info
- Home Assistant: `http://192.168.2.97:8123` (also `http://localhost:8123` from this machine)
- SmartHub API: `http://localhost:3099`
- `homeassistant.local` does NOT resolve on most LAN devices. Always use `192.168.2.97` when giving URLs to the user.
