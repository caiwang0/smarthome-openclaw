# P1V2 Smart Cooker

## Device Info

- **Name:** P1V2 Smart Cooker
- **Type:** Smart multi-cooker (rice cooker)
- **Model:** P1V2
- **Integration:** Xiaomi Home (`xiaomi_home`)
- **Primary Entity:** Look up via `ha_search_entities` — pattern: `sensor.xiaomi_*_p1v2_status_*`

## Commands

### Cancel cooking
```
Tool: ha_call_service
  domain: "button"
  service: "press"
  entity_id: "<cancel_cooking_button_entity>"
```

### Set cooking mode
```
Tool: ha_call_service
  domain: "select"
  service: "select_option"
  entity_id: "<mode_select_entity>"
  data: {"option": "<mode_value>"}
```
Look up available cooking modes from the entity's attributes via `ha_get_state`.

### Set cook time
```
Tool: ha_call_service
  domain: "number"
  service: "set_value"
  entity_id: "<cook_time_entity>"
  data: {"value": 30}
```

### Set keep warm temperature
```
Tool: ha_call_service
  domain: "number"
  service: "set_value"
  entity_id: "<keep_warm_temp_entity>"
  data: {"value": 65}
```

### Set keep warm duration
```
Tool: ha_call_service
  domain: "number"
  service: "set_value"
  entity_id: "<keep_warm_time_entity>"
  data: {"value": 60}
```

### Toggle auto keep warm
```
Tool: ha_call_service
  domain: "switch"
  service: "turn_on"
  entity_id: "<auto_keep_warm_entity>"
```

### Toggle alarm/beep
```
Tool: ha_call_service
  domain: "switch"
  service: "turn_off"
  entity_id: "<alarm_entity>"
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
