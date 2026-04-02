# MA8 Air Conditioner

## Device Info

- **Name:** MA8 Air Conditioner
- **Type:** `climate` + switches/sensors
- **Model:** MA8
- **Integration:** Xiaomi Home (`xiaomi_home`)
- **Primary Entity:** Look up via `/api/devices` — pattern: `climate.xiaomi_*_ma8`

## Commands

> Read the API port first: `API_PORT=$(grep API_PORT .env | cut -d= -f2)`

### Power
```bash
# Turn on
curl -s -X POST http://localhost:${API_PORT}/api/services/climate/turn_on \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "<entity_id>"}'

# Turn off
curl -s -X POST http://localhost:${API_PORT}/api/services/climate/turn_off \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "<entity_id>"}'
```

### Set temperature and mode
```bash
curl -s -X POST http://localhost:${API_PORT}/api/services/climate/set_temperature \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "<entity_id>", "temperature": 24, "hvac_mode": "cool"}'
```

### Set HVAC mode
```bash
# Modes: off, cool, heat, heat_cool, auto, dry, fan_only
curl -s -X POST http://localhost:${API_PORT}/api/services/climate/set_hvac_mode \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "<entity_id>", "hvac_mode": "cool"}'
```

### Fan mode
```bash
curl -s -X POST http://localhost:${API_PORT}/api/services/select/select_option \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "<fan_mode_select_entity>", "option": "<mode_value>"}'
```
Look up available options from the entity's attributes via `/api/devices`.

### Horizontal swing
```bash
# Toggle horizontal swing on/off
curl -s -X POST http://localhost:${API_PORT}/api/services/switch/turn_on \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "<horizontal_swing_entity>"}'
```

### Child lock (physical controls lock)
```bash
# Lock
curl -s -X POST http://localhost:${API_PORT}/api/services/switch/turn_on \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "<physical_controls_locked_entity>"}'

# Unlock
curl -s -X POST http://localhost:${API_PORT}/api/services/switch/turn_off \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "<physical_controls_locked_entity>"}'
```

### Delay timer
```bash
# Enable delay
curl -s -X POST http://localhost:${API_PORT}/api/services/switch/turn_on \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "<delay_switch_entity>"}'

# Set delay time (minutes)
curl -s -X POST http://localhost:${API_PORT}/api/services/number/set_value \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "<delay_time_entity>", "value": 30}'
```

### Indicator light
```bash
curl -s -X POST http://localhost:${API_PORT}/api/services/light/turn_off \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "<indicator_light_entity>"}'
```

### Key entities

| Purpose | Entity pattern | Domain |
|---------|---------------|--------|
| Main climate control | `climate.xiaomi_*_ma8` | climate |
| Fan/mode select | `select.xiaomi_*_ma8_mode_*` | select |
| Horizontal swing | `switch.xiaomi_*_ma8_horizontal_swing_*` | switch |
| Child/panel lock | `switch.xiaomi_*_ma8_physical_controls_locked_*` | switch |
| Alarm/beep | `switch.xiaomi_*_ma8_alarm_*` | switch |
| Delay timer toggle | `switch.xiaomi_*_ma8_delay_*` | switch |
| Delay time (minutes) | `number.xiaomi_*_ma8_delay_time_*` | number |
| Indicator light | `light.xiaomi_*_ma8_*indicator_light` | light |
| Fault code | `sensor.xiaomi_*_ma8_fault_*` | sensor |

## Quirks

- None known yet.
