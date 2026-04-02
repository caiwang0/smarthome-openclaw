# Automations — JSON Reference

> This file contains the full JSON schema, trigger/condition/action type examples, and automation templates.
> For the creation workflow and required details checklist, see `_guide.md`.

---

## Automation JSON Schema

```json
{
  "id": "unique_slug_id",
  "alias": "Human-readable name",
  "description": "What this automation does",
  "mode": "single",
  "trigger": [ ... ],
  "condition": [ ... ],
  "action": [ ... ]
}
```

| Field | Required | Description |
|---|---|---|
| `id` | Yes | Unique string slug. Must match the URL path. Use snake_case. |
| `alias` | Yes | Human-readable name shown in HA UI |
| `description` | No | Free text explaining the purpose |
| `mode` | No | `single` (default), `restart`, `queued`, `parallel` |
| `trigger` | Yes | Array of trigger objects (OR logic — any trigger fires the automation) |
| `condition` | No | Array of condition objects (AND logic — all must be true) |
| `action` | Yes | Array of action objects (executed sequentially) |

---

## Trigger Types

Use **platform triggers** (not device triggers) for maximum compatibility.

### Time trigger
Fires at a specific time every day.
```json
{
  "platform": "time",
  "at": "23:00:00"
}
```

### Time pattern trigger
Fires on a recurring schedule.
```json
{
  "platform": "time_pattern",
  "minutes": "/30"
}
```
- `"/30"` = every 30 minutes
- `"/5"` = every 5 minutes
- `"*"` = every minute (for that field)

### State trigger
Fires when an entity's state changes. Only `entity_id` is required — `to`, `from`, `attribute`, and `for` are all optional. If `to`/`from` are omitted, it fires on **any** state change.
```json
{
  "platform": "state",
  "entity_id": "light.living_room",
  "to": "on"
}
```

With optional `from` and duration (`for`):
```json
{
  "platform": "state",
  "entity_id": "media_player.xiaomi_tv",
  "to": "playing",
  "for": "00:05:00"
}
```

### Numeric state trigger
Fires when a numeric value crosses a threshold.
```json
{
  "platform": "numeric_state",
  "entity_id": "sensor.temperature",
  "above": 30
}
```

With both bounds:
```json
{
  "platform": "numeric_state",
  "entity_id": "sensor.humidity",
  "below": 40,
  "for": "00:10:00"
}
```

Using an attribute instead of the main state:
```json
{
  "platform": "numeric_state",
  "entity_id": "climate.living_room_ac",
  "attribute": "current_temperature",
  "above": 32
}
```

### Sun trigger
Fires at sunrise or sunset with optional offset.
```json
{
  "platform": "sun",
  "event": "sunset",
  "offset": "-00:30:00"
}
```
- `"offset": "-00:30:00"` = 30 minutes before sunset
- `"offset": "01:00:00"` = 1 hour after

### Template trigger
Fires when a Jinja2 template evaluates to true.
```json
{
  "platform": "template",
  "value_template": "{{ states('sensor.temperature') | float > 30 and is_state('climate.ac', 'off') }}"
}
```

### Home Assistant trigger
Fires on HA startup or shutdown.
```json
{
  "platform": "homeassistant",
  "event": "start"
}
```

### Zone trigger
Fires when a person/device_tracker enters or leaves a zone.
```json
{
  "platform": "zone",
  "entity_id": "person.owner",
  "zone": "zone.home",
  "event": "enter"
}
```

### Calendar trigger
Fires on calendar event start or end.
```json
{
  "platform": "calendar",
  "entity_id": "calendar.personal",
  "event": "start",
  "offset": "-00:15:00"
}
```

### Event trigger
Fires on a Home Assistant bus event.
```json
{
  "platform": "event",
  "event_type": "custom_event_name",
  "event_data": {
    "key": "value"
  }
}
```

### Webhook trigger
Fires when an HTTP webhook is called.
```json
{
  "platform": "webhook",
  "webhook_id": "my_automation_hook",
  "allowed_methods": ["POST"],
  "local_only": true
}
```

### MQTT trigger
Fires on MQTT message.
```json
{
  "platform": "mqtt",
  "topic": "home/sensor/temperature",
  "payload": "on"
}
```

### Tag trigger
Fires when an NFC/RFID tag is scanned.
```json
{
  "platform": "tag",
  "tag_id": ["my_tag_id"]
}
```

---

## Condition Types

Conditions are optional. All conditions must be true (AND logic) for the action to run.

### State condition
```json
{
  "condition": "state",
  "entity_id": "light.living_room",
  "state": "on"
}
```

### Numeric state condition
```json
{
  "condition": "numeric_state",
  "entity_id": "sensor.temperature",
  "above": 25
}
```

### Time condition
```json
{
  "condition": "time",
  "after": "22:00:00",
  "before": "06:00:00",
  "weekday": ["mon", "tue", "wed", "thu", "fri"]
}
```

### Sun condition
```json
{
  "condition": "sun",
  "after": "sunset",
  "after_offset": "-01:00:00"
}
```

### Template condition
```json
{
  "condition": "template",
  "value_template": "{{ states('sensor.occupancy') == 'on' }}"
}
```

### OR condition (any sub-condition true)
```json
{
  "condition": "or",
  "conditions": [
    { "condition": "state", "entity_id": "person.owner", "state": "home" },
    { "condition": "numeric_state", "entity_id": "sensor.temperature", "above": 35 }
  ]
}
```

---

## Action Types

### Service call (most common)
```json
{
  "service": "light.turn_off",
  "target": {
    "entity_id": "light.living_room"
  }
}
```

With service data:
```json
{
  "service": "light.turn_on",
  "target": {
    "entity_id": "light.bedroom"
  },
  "data": {
    "brightness": 128
  }
}
```

### Target multiple entities
```json
{
  "service": "light.turn_off",
  "target": {
    "entity_id": [
      "light.living_room",
      "light.bedroom",
      "light.kitchen"
    ]
  }
}
```

### Target an entire area
```json
{
  "service": "light.turn_off",
  "target": {
    "area_id": "living_room"
  }
}
```

### Delay
```json
{
  "delay": "00:00:30"
}
```

### Choose (if/else)
```json
{
  "choose": [
    {
      "conditions": [
        { "condition": "numeric_state", "entity_id": "sensor.temperature", "above": 30 }
      ],
      "sequence": [
        { "service": "climate.set_temperature", "target": { "entity_id": "climate.ac" }, "data": { "temperature": 24 } }
      ]
    }
  ],
  "default": [
    { "service": "climate.turn_off", "target": { "entity_id": "climate.ac" } }
  ]
}
```

---

## Common Automation Templates

### Turn off all lights at a specific time
```json
{
  "id": "all_lights_off_midnight",
  "alias": "Turn off all lights at midnight",
  "description": "Turns off every light in the house at midnight",
  "trigger": [
    { "platform": "time", "at": "00:00:00" }
  ],
  "condition": [],
  "action": [
    { "service": "light.turn_off", "target": { "entity_id": "all" } }
  ]
}
```

### Turn on AC when temperature is too high
```json
{
  "id": "ac_on_when_hot",
  "alias": "Turn on AC when temperature exceeds 30°C",
  "description": "Activates AC in cool mode at 24°C when room temp goes above 30",
  "trigger": [
    {
      "platform": "numeric_state",
      "entity_id": "sensor.room_temperature",
      "above": 30,
      "for": "00:05:00"
    }
  ],
  "condition": [],
  "action": [
    {
      "service": "climate.set_hvac_mode",
      "target": { "entity_id": "climate.living_room_ac" },
      "data": { "hvac_mode": "cool" }
    },
    {
      "service": "climate.set_temperature",
      "target": { "entity_id": "climate.living_room_ac" },
      "data": { "temperature": 24 }
    }
  ]
}
```

### Turn on lights at sunset
```json
{
  "id": "lights_on_sunset",
  "alias": "Turn on living room lights at sunset",
  "description": "Turns on living room light 30 minutes before sunset",
  "trigger": [
    { "platform": "sun", "event": "sunset", "offset": "-00:30:00" }
  ],
  "condition": [],
  "action": [
    {
      "service": "light.turn_on",
      "target": { "entity_id": "light.living_room" },
      "data": { "brightness": 200 }
    }
  ]
}
```

### Goodnight routine (multi-action)
```json
{
  "id": "goodnight_routine",
  "alias": "Goodnight routine",
  "description": "Turns off all lights, sets AC to sleep mode",
  "trigger": [
    { "platform": "time", "at": "23:30:00" }
  ],
  "condition": [],
  "action": [
    { "service": "light.turn_off", "target": { "entity_id": "all" } },
    {
      "service": "climate.set_hvac_mode",
      "target": { "entity_id": "climate.bedroom_ac" },
      "data": { "hvac_mode": "cool" }
    },
    {
      "service": "climate.set_temperature",
      "target": { "entity_id": "climate.bedroom_ac" },
      "data": { "temperature": 26 }
    },
    {
      "service": "media_player.turn_off",
      "target": { "entity_id": "media_player.xiaomi_tv" }
    }
  ]
}
```

### Motion-activated light
```json
{
  "id": "hallway_motion_light",
  "alias": "Turn on hallway light on motion",
  "description": "Turns on hallway light when motion detected, off after 5 min of no motion",
  "mode": "restart",
  "trigger": [
    {
      "platform": "state",
      "entity_id": "binary_sensor.hallway_motion",
      "to": "on"
    }
  ],
  "condition": [],
  "action": [
    {
      "service": "light.turn_on",
      "target": { "entity_id": "light.hallway" }
    },
    { "delay": "00:05:00" },
    {
      "service": "light.turn_off",
      "target": { "entity_id": "light.hallway" }
    }
  ]
}
```

Note: `"mode": "restart"` means if motion is detected again during the 5-minute wait, the automation restarts (resets the timer).
