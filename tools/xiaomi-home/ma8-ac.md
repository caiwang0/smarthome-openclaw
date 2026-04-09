# MA8 Air Conditioner

## Device Info

- **Name:** MA8 Air Conditioner
- **Type:** `climate` + switches/sensors
- **Model:** MA8
- **Integration:** Xiaomi Home (`xiaomi_home`)
- **Primary Entity:** Look up via `ha_search_entities` — pattern: `climate.xiaomi_*_ma8`

## Commands

### Power
```
# Turn on
Tool: ha_call_service
  domain: "climate"
  service: "turn_on"
  entity_id: "<entity_id>"

# Turn off
Tool: ha_call_service
  domain: "climate"
  service: "turn_off"
  entity_id: "<entity_id>"
```

### Set temperature and mode
```
Tool: ha_call_service
  domain: "climate"
  service: "set_temperature"
  entity_id: "<entity_id>"
  data: {"temperature": 24, "hvac_mode": "cool"}
```

### Set HVAC mode
```
# Modes: off, cool, heat, heat_cool, auto, dry, fan_only
Tool: ha_call_service
  domain: "climate"
  service: "set_hvac_mode"
  entity_id: "<entity_id>"
  data: {"hvac_mode": "cool"}
```

### Fan mode
```
Tool: ha_call_service
  domain: "select"
  service: "select_option"
  entity_id: "<fan_mode_select_entity>"
  data: {"option": "<mode_value>"}
```
Look up available options from the entity's attributes via `ha_get_state`.

### Horizontal swing
```
# Toggle horizontal swing on/off
Tool: ha_call_service
  domain: "switch"
  service: "turn_on"
  entity_id: "<horizontal_swing_entity>"
```

### Child lock (physical controls lock)
```
# Lock
Tool: ha_call_service
  domain: "switch"
  service: "turn_on"
  entity_id: "<physical_controls_locked_entity>"

# Unlock
Tool: ha_call_service
  domain: "switch"
  service: "turn_off"
  entity_id: "<physical_controls_locked_entity>"
```

### Delay timer
```
# Enable delay
Tool: ha_call_service
  domain: "switch"
  service: "turn_on"
  entity_id: "<delay_switch_entity>"

# Set delay time (minutes)
Tool: ha_call_service
  domain: "number"
  service: "set_value"
  entity_id: "<delay_time_entity>"
  data: {"value": 30}
```

### Indicator light
```
Tool: ha_call_service
  domain: "light"
  service: "turn_off"
  entity_id: "<indicator_light_entity>"
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
