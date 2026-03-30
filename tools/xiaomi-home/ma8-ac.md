# MA8 Air Conditioner

## Device Info

- **Name:** MA8 Air Conditioner
- **Device ID:** `646997784`
- **Type:** `climate` + switches/sensors
- **Model:** MA8
- **Integration:** Xiaomi Home (`xiaomi_home`)
- **Primary Entity:** `climate.xiaomi_cn_646997784_ma8`

## Commands

### Set HVAC mode / temperature
```bash
HA_TOKEN=$(grep HA_TOKEN .env | cut -d= -f2)

# Turn on
curl -s -X POST http://localhost:8123/api/services/climate/turn_on \
  -H "Authorization: Bearer $HA_TOKEN" -H "Content-Type: application/json" \
  -d '{"entity_id": "climate.xiaomi_cn_646997784_ma8"}'

# Turn off
curl -s -X POST http://localhost:8123/api/services/climate/turn_off \
  -H "Authorization: Bearer $HA_TOKEN" -H "Content-Type: application/json" \
  -d '{"entity_id": "climate.xiaomi_cn_646997784_ma8"}'

# Set temperature (e.g. 24°C, cool mode)
curl -s -X POST http://localhost:8123/api/services/climate/set_temperature \
  -H "Authorization: Bearer $HA_TOKEN" -H "Content-Type: application/json" \
  -d '{"entity_id": "climate.xiaomi_cn_646997784_ma8", "temperature": 24, "hvac_mode": "cool"}'
```

### Key entities
| Entity | Purpose |
|--------|---------|
| `climate.xiaomi_cn_646997784_ma8` | Main climate control |
| `select.xiaomi_cn_646997784_ma8_mode_p_2_4` | Fan/mode select |
| `switch.xiaomi_cn_646997784_ma8_horizontal_swing_p_8_3` | Horizontal swing |
| `switch.xiaomi_cn_646997784_ma8_physical_controls_locked_p_5_1` | Child/panel lock |
| `switch.xiaomi_cn_646997784_ma8_alarm_p_6_1` | Alarm/beep |
| `switch.xiaomi_cn_646997784_ma8_delay_p_9_1` | Delay timer |
| `number.xiaomi_cn_646997784_ma8_delay_time_p_9_2` | Delay time (minutes) |
| `light.xiaomi_cn_646997784_ma8_s_10_indicator_light` | Indicator light |
| `sensor.xiaomi_cn_646997784_ma8_fault_p_2_2` | Fault code |

## Quirks

- None known yet.
