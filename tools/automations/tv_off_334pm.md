# Turn off TV at 3:34 PM

- **ID:** `tv_off_334pm`
- **Created:** 2026-03-30
- **Trigger:** Every day at 15:34:00 (3:34 PM SGT)
- **Condition:** None
- **Action:** Turn off edgenesis-tv
- **Entities:** `media_player.xiaomi_cn_mitv_3b1ed2f92de5175e4cdf6f66d685ec5c_7508121deb5745f19aa3b22537292b13_v1`

## Raw JSON

```json
{
  "id": "tv_off_334pm",
  "alias": "Turn off TV at 3:34 PM",
  "description": "Turns off the Xiaomi TV every day at 3:34 PM SGT",
  "mode": "single",
  "trigger": [
    {
      "platform": "time",
      "at": "15:34:00"
    }
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
