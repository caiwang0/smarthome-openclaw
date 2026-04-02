# P1V2 Smart Cooker

## Device Info

- **Name:** P1V2 Smart Cooker
- **Type:** Smart multi-cooker (rice cooker)
- **Model:** P1V2
- **Integration:** Xiaomi Home (`xiaomi_home`)
- **Primary Entity:** Look up via `/api/devices` — pattern: `sensor.xiaomi_*_p1v2_status_*`

## Commands

> Read the API port first: `API_PORT=$(grep API_PORT .env | cut -d= -f2)`

### Cancel cooking
```bash
curl -s -X POST http://localhost:${API_PORT}/api/services/button/press \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "<cancel_cooking_button_entity>"}'
```

### Set cooking mode
```bash
curl -s -X POST http://localhost:${API_PORT}/api/services/select/select_option \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "<mode_select_entity>", "option": "<mode_value>"}'
```
Look up available cooking modes from the entity's attributes via `/api/devices`.

### Set cook time
```bash
curl -s -X POST http://localhost:${API_PORT}/api/services/number/set_value \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "<cook_time_entity>", "value": 30}'
```

### Set keep warm temperature
```bash
curl -s -X POST http://localhost:${API_PORT}/api/services/number/set_value \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "<keep_warm_temp_entity>", "value": 65}'
```

### Set keep warm duration
```bash
curl -s -X POST http://localhost:${API_PORT}/api/services/number/set_value \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "<keep_warm_time_entity>", "value": 60}'
```

### Toggle auto keep warm
```bash
curl -s -X POST http://localhost:${API_PORT}/api/services/switch/turn_on \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "<auto_keep_warm_entity>"}'
```

### Toggle alarm/beep
```bash
curl -s -X POST http://localhost:${API_PORT}/api/services/switch/turn_off \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "<alarm_entity>"}'
```

### Key entities

| Purpose | Entity pattern | Domain |
|---------|---------------|--------|
| Cooker status | `sensor.xiaomi_*_p1v2_status_*` | sensor |
| Time remaining | `sensor.xiaomi_*_p1v2_left_time_*` | sensor |
| Current temperature | `sensor.xiaomi_*_p1v2_temperature_*` | sensor |
| Current cook mode | `sensor.xiaomi_*_p1v2_current_cook_mode_*` | sensor |
| Current cooking step | `sensor.xiaomi_*_p1v2_current_step_*` | sensor |
| Step time remaining | `sensor.xiaomi_*_p1v2_step_left_time_*` | sensor |
| Cooking mode select | `select.xiaomi_*_p1v2_mode_*` | select |
| Cook mode select | `select.xiaomi_*_p1v2_cook_mode_*` | select |
| Cook time | `number.xiaomi_*_p1v2_cook_time_*` | number |
| Keep warm temperature | `number.xiaomi_*_p1v2_keep_warm_temperature_*` | number |
| Keep warm duration | `number.xiaomi_*_p1v2_keep_warm_time_*` | number |
| Reservation time left | `number.xiaomi_*_p1v2_reservation_left_time_*` | number |
| Working level | `number.xiaomi_*_p1v2_working_level_*` | number |
| Auto keep warm | `switch.xiaomi_*_p1v2_auto_keep_warm_*` | switch |
| Alarm/beep | `switch.xiaomi_*_p1v2_alarm_*` | switch |
| Cooking finished event | `event.xiaomi_*_p1v2_cooking_finished_*` | event |
| Cancel cooking | `button.xiaomi_*_p1v2_cancel_cooking_*` | button |

## Quirks

- None known yet.
