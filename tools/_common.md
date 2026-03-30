# Common — Shared API & Network Reference

## SmartHub API (convenience layer)

Base URL: `http://localhost:3099`

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

## Home Assistant Direct API

Base URL: `http://localhost:8123`

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

## Network Info

- Home Assistant: `http://192.168.2.97:8123` (also `http://localhost:8123` from this machine)
- SmartHub API: `http://localhost:3099`
- `homeassistant.local` does NOT resolve on most LAN devices. Always use `192.168.2.97` when giving URLs to the user.
