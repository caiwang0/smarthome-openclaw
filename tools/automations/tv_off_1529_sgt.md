# Turn off TV at 3:29 PM

- **ID:** `tv_off_1529_sgt`
- **Created:** 2026-03-30
- **Trigger:** Every day at 15:29 SGT (Asia/Singapore)
- **Condition:** None
- **Action:** Turn off Xiaomi TV
- **Entities:** `media_player.xiaomi_cn_mitv_3b1ed2f92de5175e4cdf6f66d685ec5c_7508121deb5745f19aa3b22537292b13_v1`

## Raw JSON

```json
{
  "id": "tv_off_1529_sgt",
  "alias": "Turn off TV at 3:29 PM",
  "description": "Turns off Xiaomi TV every day at 15:29 SGT",
  "mode": "single",
  "trigger": [
    { "platform": "time", "at": "15:29:00" }
  ],
  "condition": [],
  "action": [
    {
      "service": "media_player.turn_off",
      "target": {
        "entity_id": "media_player.xiaomi_cn_mitv_3b1ed2f92de5175e4cdf6f66d685ec5c_7508121deb5745f19aa3b22537292b13_v1"
      }
    }
  ]
}
```
