# Common — Shared API & Network Reference

> **Before running any command below**, read the API port from `.env`:
> ```bash
> API_PORT=$(grep API_PORT .env | cut -d= -f2)
> ```
> All curl examples below use `${API_PORT}`. Never hardcode port 3001 — it may differ per installation.

## SmartHub API (convenience layer)

Base URL: `http://localhost:${API_PORT}`

### List all devices
```bash
curl -s http://localhost:${API_PORT}/api/devices | jq '.devices[] | {name, device_type, status, area_name, primary_entity}'
```

### Get a specific device
```bash
curl -s http://localhost:${API_PORT}/api/devices/<device_id>
```

### Control a device (call a service)
```bash
curl -s -X POST http://localhost:${API_PORT}/api/services/<domain>/<service> \
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
curl -s http://localhost:${API_PORT}/api/areas | jq '.areas'
```

---

## Home Assistant Direct API

Base URL: `http://localhost:8123`

**Authentication header (required for all HA calls):**
```bash
HA_TOKEN=$(grep HA_TOKEN .env | cut -d= -f2)
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

- Home Assistant: `http://localhost:8123`
- SmartHub API: `http://localhost:${API_PORT}` (read `API_PORT` from `.env`; default 3001)
- For browser access from other devices on the LAN, use the Pi's IP address (run `hostname -I | awk '{print $1}'` to find it)
- `homeassistant.local` does NOT resolve on most LAN devices. Use the Pi's IP instead when giving URLs to the user.
