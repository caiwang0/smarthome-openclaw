# Automations — Skill Guide

## Workflow: How to Create an Automation

When a user asks for an automation (e.g., "turn off lights at midnight"), follow these steps:

1. **Understand the intent** — Parse the user's request into: trigger (when), condition (if), action (what)
2. **Check for missing details** — Use the **Required Details Checklist** below to verify you have everything needed. If any required detail is missing or ambiguous, ask the user BEFORE drafting. Do NOT guess or fill in defaults.
3. **Look up entity IDs** — Read the relevant device skill files in `tools/` to get the correct entity IDs. Never guess.
4. **Draft the automation JSON** — Use the schema and examples below
5. **Show the user a summary** — Present in plain language: "At midnight every day → turn off living room light. Want me to create this?"
6. **Wait for confirmation** — Do NOT create until the user says yes
7. **Create via API** — POST the JSON to HA
8. **Confirm success** — Tell the user the automation is active
9. **Update skill files** — Add the automation to `tools/automations/` as a record

---

## REST API Reference

**Authentication for all calls:**
```bash
HA_TOKEN=$(grep HA_TOKEN .env | cut -d= -f2)
```

### Create an automation
```bash
curl -s -X POST http://localhost:8123/api/config/automation/config/<automation_id> \
  -H "Authorization: Bearer $HA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<JSON payload>'
```
The `<automation_id>` in the URL must match the `id` field in the JSON body. Use a descriptive slug (e.g., `lights_off_midnight`, `ac_on_when_hot`).

### Delete an automation
```bash
curl -s -X DELETE http://localhost:8123/api/config/automation/config/<automation_id> \
  -H "Authorization: Bearer $HA_TOKEN"
```

### Enable an automation
```bash
curl -s -X POST http://localhost:8123/api/services/automation/turn_on \
  -H "Authorization: Bearer $HA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "automation.<automation_id>"}'
```

### Disable an automation
```bash
curl -s -X POST http://localhost:8123/api/services/automation/turn_off \
  -H "Authorization: Bearer $HA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "automation.<automation_id>"}'
```

### Manually trigger an automation
```bash
curl -s -X POST http://localhost:8123/api/services/automation/trigger \
  -H "Authorization: Bearer $HA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "automation.<automation_id>"}'
```

### Reload all automations (after manual YAML edits)
```bash
curl -s -X POST http://localhost:8123/api/services/automation/reload \
  -H "Authorization: Bearer $HA_TOKEN"
```

### List all automations
```bash
curl -s http://localhost:8123/api/states \
  -H "Authorization: Bearer $HA_TOKEN" | jq '[.[] | select(.entity_id | startswith("automation.")) | {entity_id, state, attributes: {friendly_name: .attributes.friendly_name, last_triggered: .attributes.last_triggered}}]'
```

---

## Required Details Checklist

**Source: Verified against HA Core automation schema and REST API docs.**

Before drafting any automation, match the user's request to the tables below. Every **Required** field must be explicitly provided or confirmed by the user. If missing, **ask** — don't assume.

### Every automation needs:

| Detail | Required by HA API | What to ask if missing |
|--------|-------------------|----------------------|
| **`id`** — unique slug | Yes (must match URL path) | Auto-generate from intent, e.g., `lights_off_midnight` |
| **`trigger`** (or `triggers`) — when it fires | Yes, at least one | Determine from context, then check trigger-specific table below |
| **`action`** (or `actions`) — what to do | Yes, at least one | "What should happen? (e.g., turn off TV, set AC to 24°C)" |
| **Action target device(s)** | Yes (in action's `target`) | "Which device? I see: [list matching devices from skill files]" |
| **`alias`** — friendly name | Optional but recommended | Auto-generate from intent |
| **`condition`** (or `conditions`) | Optional | See "Optional but worth asking" below |
| **`mode`** | Optional, default `single` | Only ask if relevant (see below) |

### Per-trigger required fields (from HA API schema):

| Platform | Required fields | Optional fields | User sounds like… | Ask if missing |
|---|---|---|---|---|
| **`time`** | `at` (HH:MM, HH:MM:SS, or input_datetime entity) | `weekday` (mon-sun list) | "at night", "every evening" | "What exact time?" |
| **`time_pattern`** | At least one of: `hours`, `minutes`, `seconds` (int, `"*"`, or `"/N"`) | — | "every 30 min", "periodically" | "How often?" |
| **`state`** | `entity_id` | `to`, `from`, `not_to`, `not_from`, `attribute`, `for` | "when TV turns on", "when door opens" | "Which device?" (`to` is optional — fires on ANY state change if omitted, so ask: "Any specific state, or any change?") |
| **`numeric_state`** | `entity_id` + at least one of `above`/`below` | `attribute`, `value_template`, `for` | "when it's hot", "battery low" | "What value?" / "Above or below?" |
| **`sun`** | `event` (`sunrise` or `sunset`) | `offset` (e.g., `"-00:30:00"`) | "at sunset", "when dark" | "Sunrise or sunset?" / "Any offset?" |
| **`zone`** | `entity_id` (person/device_tracker) + `zone` + `event` (`enter`/`leave`) | — | "when I get home", "when I leave" | "Which person?" / "Which zone?" / "Enter or leave?" |
| **`calendar`** | `entity_id` (calendar entity) | `event` (`start`/`end`), `offset` | "when my meeting starts" | "Which calendar?" |
| **`template`** | `value_template` (Jinja2) | `for` | Complex conditions | Build from user's description |
| **`event`** | `event_type` | `event_data`, `event_context` | "when X event fires" | "What event type?" |
| **`webhook`** | `webhook_id` | `allowed_methods`, `local_only` | "when webhook is called" | "What webhook ID?" |
| **`mqtt`** | `topic` | `payload`, `value_template`, `encoding`, `qos` | "when MQTT message arrives" | "What topic?" |
| **`tag`** | `tag_id` | `device_id` | "when NFC tag is scanned" | "Which tag?" |
| **`device`** | `device_id` + `domain` + `type` | Varies by integration | "when button is pressed" | Check device's integration docs |
| **`homeassistant`** | `event` (`start` or `shutdown`) | — | "when HA restarts" | "On startup or shutdown?" |

### Common `for` modifier (applies to state, numeric_state, template):

`for` means "only fire if the condition has been true for this long." Format: `HH:MM:SS` or `{ hours, minutes, seconds }`.

User says "for more than 10 minutes" → add `"for": "00:10:00"` to the trigger. Ask: "How long should the condition hold before triggering?"

### Optional but worth asking about:

| Detail | When to ask |
|--------|------------|
| **Conditions** (time window, weekday, only-if) | If the automation could plausibly need limits — e.g., "turn on lights at sunset" → "Only on weekdays, or every day?" |
| **Multiple actions** | If the trigger implies a routine — e.g., "goodnight" → "Anything else besides turning off lights?" |
| **`mode`** (`single`/`restart`/`queued`/`parallel`) | Only if the automation involves delays or could retrigger — e.g., motion-activated light → use `restart` |
| **`for` duration** | If the user says "when it's been hot for a while" — ask how long |

### Examples of what to ask:

| User says | Missing (per API schema) | Ask |
|---|---|---|
| "turn off the lights at night" | `time` trigger needs `at` ; action needs target entity | "What time exactly? And all lights or specific ones?" |
| "turn on AC when it's hot" | `numeric_state` needs `above` or `below` | "At what temperature? e.g., above 30°C?" |
| "notify me when the door opens" | `state` trigger needs `entity_id` | "Which door? I see: [list door sensors]" |
| "turn off TV after a while" | Unclear trigger — could be `state` with `for`, or `time` | "After how long idle? e.g., 30 minutes of no activity?" |
| "dim the lights in the evening" | `time` needs `at` ; `light.turn_on` needs `brightness` (0-255) | "What time? And what brightness level?" |
| "when I get home turn on the lights" | `zone` needs `entity_id` (person) + `zone` | "Which person entity tracks you? And which zone is 'home'?" |

---

For the full JSON schema, all trigger/condition/action type examples with code, and common automation templates, read `_reference.md`.

---

## Per-Domain Trigger Reference

When a user asks about a specific device type, use these triggers:

### Lights
| User says | Trigger |
|---|---|
| "when the light turns on" | `state` → `to: "on"` |
| "when the light turns off" | `state` → `to: "off"` |
| "when brightness is above 50%" | `numeric_state` → `attribute: "brightness"`, `above: 128` |

### Climate / AC
| User says | Trigger |
|---|---|
| "when temperature is above 30" | `numeric_state` → `entity_id: sensor.*_temperature`, `above: 30` |
| "when AC turns on" | `state` → `to: "cool"` or `to: "heat"` (climate states are HVAC modes, not on/off) |
| "when humidity is high" | `numeric_state` → `entity_id: sensor.*_humidity`, `above: 70` |

Note: Climate entities use HVAC modes as states: `off`, `cool`, `heat`, `heat_cool`, `auto`, `dry`, `fan_only`. There is no "on" state.

### Media Player
| User says | Trigger |
|---|---|
| "when TV starts playing" | `state` → `to: "playing"` |
| "when TV is turned off" | `state` → `to: "off"` |
| "when TV is idle for 30 min" | `state` → `to: "idle"`, `for: "00:30:00"` |

### Sensors
| User says | Trigger |
|---|---|
| "when temperature exceeds 30" | `numeric_state` → `above: 30` |
| "when power usage is above 1000W" | `numeric_state` → `above: 1000` |
| "when battery is below 20%" | `numeric_state` → `below: 20` |

### Binary Sensors
| User says | Trigger |
|---|---|
| "when motion is detected" | `state` → `to: "on"` |
| "when door opens" | `state` → `to: "on"` |
| "when no motion for 10 min" | `state` → `to: "off"`, `for: "00:10:00"` |

---

## Recording Created Automations

After successfully creating an automation, create a record file at `tools/automations/<automation_id>.md`:

```markdown
# <Alias>

- **ID:** `<automation_id>`
- **Created:** <date>
- **Trigger:** <plain language description>
- **Condition:** <plain language, or "None">
- **Action:** <plain language description>
- **Entities:** <list of entity_ids involved>

## Raw JSON

<the full JSON payload used to create it>
```

This lets you (and the user) review, modify, or recreate automations later.

---

## Important Notes

- **Always look up entity IDs** from the device skill files in `tools/`. Never guess or make up entity IDs.
- **Climate states are HVAC modes**, not on/off. Use `cool`, `heat`, `off`, etc.
- **Brightness is 0-255**, not 0-100%. Convert percentages: `brightness = percentage * 2.55`.
- **`for` durations** use `HH:MM:SS` format. They mean "only fire if the condition has been true for this long."
- **`entity_id: "all"`** targets every entity in a domain (e.g., `light.turn_off` with `all` turns off every light).
- **The `id` field must be unique** across all automations. Use descriptive snake_case slugs.
- **Automations are written to `automations.yaml`** by HA and persist across restarts.
