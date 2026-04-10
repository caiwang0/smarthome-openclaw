# Xiaomi TV

## Device Info

- **Name:** Xiaomi TV
- **Device ID:** `edgenesis-tv`
- **Type:** `media_player` (DLNA)
- **Model:** `xiaomi.tv.v1`
- **Integration:** Xiaomi Home (`xiaomi_home`)
- **Primary Entity:** Look up via `ha_search_entities` — entity IDs are long and auto-generated.

## Commands

### Power
```
Tool: ha_call_service
  domain: "media_player"
  service: "turn_off"
  entity_id: "<entity_id>"
```

### Volume
```
# Volume up
Tool: ha_call_service
  domain: "media_player"
  service: "volume_up"
  entity_id: "<entity_id>"

# Volume down
Tool: ha_call_service
  domain: "media_player"
  service: "volume_down"
  entity_id: "<entity_id>"

# Set volume (0.0 to 1.0)
Tool: ha_call_service
  domain: "media_player"
  service: "volume_set"
  entity_id: "<entity_id>"
  data: {"volume_level": 0.5}

# Mute/unmute
Tool: ha_call_service
  domain: "media_player"
  service: "volume_mute"
  entity_id: "<entity_id>"
  data: {"is_volume_muted": true}
```

### Playback
```
# Play
Tool: ha_call_service
  domain: "media_player"
  service: "media_play"
  entity_id: "<entity_id>"

# Pause
Tool: ha_call_service
  domain: "media_player"
  service: "media_pause"
  entity_id: "<entity_id>"
```

## Quirks

- **Frequently shows "unavailable"** — The DLNA connection drops often, but the TV still accepts commands. Try the command anyway before telling the user it's offline.
- **Cannot power on via network** — When the TV is in standby, Wi-Fi disconnects. There is no way to wake it over the network. This requires an IR blaster (not yet set up).
- **Entity ID is very long** — Never guess the entity ID. Always look it up via `ha_search_entities`.
