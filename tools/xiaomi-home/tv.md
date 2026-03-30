# Xiaomi TV

## Device Info

- **Name:** Xiaomi TV
- **Device ID:** `edgenesis-tv`
- **Type:** `media_player` (DLNA)
- **Model:** `xiaomi.tv.v1`
- **Integration:** Xiaomi Home (`xiaomi_home`)
- **Primary Entity:** Look up via `/api/devices` — entity IDs are long and auto-generated.

## Commands

### Power
```bash
# Turn off (standby)
curl -s -X POST http://localhost:3099/api/services/media_player/turn_off \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "<entity_id>"}'
```

### Volume
```bash
# Volume up
curl -s -X POST http://localhost:3099/api/services/media_player/volume_up \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "<entity_id>"}'

# Volume down
curl -s -X POST http://localhost:3099/api/services/media_player/volume_down \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "<entity_id>"}'

# Set volume (0.0 to 1.0)
curl -s -X POST http://localhost:3099/api/services/media_player/volume_set \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "<entity_id>", "volume_level": 0.5}'

# Mute/unmute
curl -s -X POST http://localhost:3099/api/services/media_player/volume_mute \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "<entity_id>", "is_volume_muted": true}'
```

### Playback
```bash
# Play
curl -s -X POST http://localhost:3099/api/services/media_player/media_play \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "<entity_id>"}'

# Pause
curl -s -X POST http://localhost:3099/api/services/media_player/media_pause \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "<entity_id>"}'
```

## Quirks

- **Frequently shows "unavailable"** — The DLNA connection drops often, but the TV still accepts commands. Try the command anyway before telling the user it's offline.
- **Cannot power on via network** — When the TV is in standby, Wi-Fi disconnects. There is no way to wake it over the network. This requires an IR blaster (not yet set up).
- **Entity ID is very long** — Never guess the entity ID. Always look it up from `/api/devices`.
