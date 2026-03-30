# P1V2 Smart Cooker

## Device Info

- **Name:** P1V2 Smart Cooker
- **Device ID:** `963397653`
- **Type:** Smart multi-cooker (rice cooker)
- **Model:** P1V2
- **Integration:** Xiaomi Home (`xiaomi_home`)
- **Primary Entity:** `sensor.xiaomi_cn_963397653_p1v2_status_p_2_1`

## Commands

### Start/cancel cooking
```bash
HA_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJkMDYzMDM3YzZiMTI0MGYyOTM2MmZmNGI1ZDA2ZDE1ZCIsImlhdCI6MTc3NDUxMTEwNiwiZXhwIjoyMDg5ODcxMTA2fQ.MMWtEXXmGNE5p_mqdn-RfLD-6j77ntZgc7r9hAvENjo"

# Cancel cooking
curl -s -X POST http://localhost:8123/api/services/button/press \
  -H "Authorization: Bearer $HA_TOKEN" -H "Content-Type: application/json" \
  -d '{"entity_id": "button.xiaomi_cn_963397653_p1v2_cancel_cooking_a_2_2"}'
```

### Key entities
| Entity | Purpose |
|--------|---------|
| `sensor.xiaomi_cn_963397653_p1v2_status_p_2_1` | Cooker status |
| `sensor.xiaomi_cn_963397653_p1v2_left_time_p_2_5` | Time remaining |
| `sensor.xiaomi_cn_963397653_p1v2_temperature_p_2_11` | Current temperature |
| `sensor.xiaomi_cn_963397653_p1v2_current_cook_mode_p_4_9` | Current cook mode |
| `sensor.xiaomi_cn_963397653_p1v2_current_step_p_4_5` | Current cooking step |
| `sensor.xiaomi_cn_963397653_p1v2_step_left_time_p_4_6` | Step time remaining |
| `select.xiaomi_cn_963397653_p1v2_mode_p_2_3` | Cooking mode |
| `select.xiaomi_cn_963397653_p1v2_cook_mode_p_2_4` | Cook mode |
| `number.xiaomi_cn_963397653_p1v2_cook_time_p_2_13` | Cook time |
| `number.xiaomi_cn_963397653_p1v2_keep_warm_temperature_p_2_7` | Keep warm temperature |
| `number.xiaomi_cn_963397653_p1v2_keep_warm_time_p_2_8` | Keep warm duration |
| `number.xiaomi_cn_963397653_p1v2_reservation_left_time_p_2_10` | Reservation time left |
| `number.xiaomi_cn_963397653_p1v2_working_level_p_2_12` | Working level |
| `switch.xiaomi_cn_963397653_p1v2_auto_keep_warm_p_2_6` | Auto keep warm |
| `switch.xiaomi_cn_963397653_p1v2_alarm_p_3_1` | Alarm/beep |
| `event.xiaomi_cn_963397653_p1v2_cooking_finished_e_2_1` | Cooking finished event |

## Quirks

- None known yet.
