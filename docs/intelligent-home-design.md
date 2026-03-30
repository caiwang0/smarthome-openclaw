# Intelligent Home — OpenClaw UX Feature Design

> **Goal:** Make OpenClaw the AI layer that demonstrates what a smart home assistant can do *beyond* basic device control. Users interact via Teams/Feishu/Discord. OpenClaw parses intent and routes commands to Home Assistant.

> **Audience:** Demo/showcase — this is built to impress, showing capabilities that basic voice assistants and HA automations alone can't replicate.

---

## Architecture Overview

5 new OpenClaw skills + 1 log file. No new services or infrastructure. Everything runs through the existing OpenClaw agent, calling the HA API at `localhost:8123`.

```
User (Discord/Teams/Feishu)
  │
  ▼
OpenClaw Agent
  │
  ├── skill: intent-router        ← parses what the user wants
  │     │
  │     ├── skill: scene-executor  ← "I'm leaving" → multi-device actions
  │     ├── skill: diagnostics     ← "Why is it hot?" → reason over sensors
  │     └── (existing device skills stay as-is)
  │
  ├── skill: proactive-monitor    ← cron: checks sensors, alerts if abnormal
  ├── skill: scene-learner        ← cron: reads command log, suggests automations
  │
  └── command-log.jsonl           ← append-only log of every action taken
```

**What stays the same:**
- Existing device skills (tools/xiaomi-home/tv.md, tools/_common.md, etc.)
- HA API access pattern (curl to localhost:8123 with bearer token)
- OpenClaw's security model (HMAC, per-user isolation)
- Automations guide (tools/automations/_guide.md)

**What's new:**
- 5 skill files in tools/
- 1 JSONL log file at tools/command-log.jsonl
- 2 cron jobs (proactive monitor + scene learner)

---

## Feature 1: Intent Router

**File:** `tools/intent-router.md`

**What it does:** Replaces dumb command matching with intent understanding. Instead of needing exact phrases like "turn off light.living_room", users can say natural things and OpenClaw figures out what they mean.

**How it works:**

The intent router is a prompt instruction that runs before any device command. It classifies user messages into categories:

| Intent Category | Example Input | Routes To |
|---|---|---|
| Direct control | "turn off the lights" | Existing device skills |
| Scene / routine | "I'm leaving for work" | scene-executor skill |
| Diagnosis / why | "Why is the bedroom hot?" | diagnostics skill |
| Status query | "What's on right now?" | HA API → formatted response |
| Automation request | "Every night at 10, dim the lights" | automations/_guide.md |
| Setup / onboarding | "I just bought a Philips Hue" | Integration config flow |
| Ambient / vague | "Make it cozy" | scene-executor (with interpretation) |

**Key design decision:** The intent router is NOT a separate service or API call. It's prompt engineering — instructions in OpenClaw's system prompt that tell it how to interpret messages and which skill file to read next. The LLM *is* the router.

**Prompt structure:**
```
When you receive a message from the user:

1. Determine the intent (control, scene, diagnosis, status, automation, setup, ambient)
2. For "scene" or "ambient" intents → read tools/scene-executor.md
3. For "diagnosis" intents → read tools/diagnostics.md
4. For all intents → after executing, append to tools/command-log.jsonl
5. For direct control → use existing device skills as today
```

---

## Feature 2: Scene Executor

**File:** `tools/scene-executor.md`

**What it does:** Handles multi-device, intent-based commands. One natural sentence triggers a coordinated set of actions across multiple devices.

**Example interactions:**

| User says | OpenClaw does |
|---|---|
| "I'm leaving for work" | Turns off all lights, sets AC to eco, locks front door, arms cameras. Confirms: "Done — lights off, AC on eco, door locked, cameras armed." |
| "Movie time" | Dims living room to 20%, turns on TV, sets soundbar to movie mode, closes blinds. |
| "Good morning" | Opens blinds, turns on kitchen lights, sets AC to 24°C, reads weather + calendar summary. |
| "Make it cozy" | Checks current conditions. If cold → heater on. Dims lights to 30%. If TV is available → ambient mode. |
| "Guests are coming" | Turns on living room + hallway lights at 80%, sets AC to 23°C, unlocks front door. |
| "Goodnight" | Turns off all lights except bedroom nightlight, locks doors, sets AC to sleep mode, arms security. |

**How it works:**

1. OpenClaw receives a scene intent (via intent router)
2. Reads `tools/scene-executor.md` for instructions
3. Pulls current device states from HA API (`/api/states`)
4. Decides which devices to act on based on:
   - The user's intent (what are they trying to achieve?)
   - Current device states (don't turn off what's already off)
   - Available devices (don't try to close blinds if there are none)
   - Context (time of day, sensor readings like temperature)
5. Executes HA service calls in sequence
6. Confirms what it did in a concise message
7. Appends each action to command-log.jsonl

**Skill file contents — what the prompt should instruct:**
```markdown
## Scene Execution Rules

1. Before acting, GET /api/states to know current device states
2. Only act on devices that exist and are online
3. Skip redundant actions (don't turn off what's already off)
4. Always confirm what you did AND what you skipped (and why)
5. If a device fails, continue with the rest and report the failure
6. Use context:
   - Time of day (morning/afternoon/evening/night)
   - Temperature sensors (is it hot? cold?)
   - Current device states
7. When interpreting vague intent ("cozy", "bright", "chill"):
   - cozy = warm lighting (30%), comfortable temperature, soft media
   - bright = all lights 100%, blinds open
   - chill = dim lights, relaxed temperature, no loud devices
   - party = lights colorful/bright, music on, temperature cool
```

**Key design decision:** Scenes are NOT pre-defined lists of actions. The LLM interprets the intent dynamically based on what devices exist and their current state. This is the core differentiator from HA's built-in scenes (which are static device-state snapshots).

---

## Feature 3: Diagnostics

**File:** `tools/diagnostics.md`

**What it does:** When a user asks "why" or reports something wrong, OpenClaw gathers data from multiple sources and reasons about the cause — like a smart home doctor.

**Example interactions:**

| User says | OpenClaw gathers | OpenClaw responds |
|---|---|---|
| "Why is the bedroom hot?" | Bedroom temp sensor, AC state, outdoor temp, window sensor, AC mode/target | "Your bedroom is 31°C but the AC is set to 28°C in fan-only mode — it's not actually cooling. Outside is 35°C. Want me to switch to cool mode?" |
| "Why won't the TV turn on?" | TV entity state, network status, power switch state | "The TV shows as 'unavailable' — it might be unplugged or the Xiaomi cloud is down. The power switch it's connected to is on. Try checking the physical connection." |
| "Something is using a lot of power" | All switch/plug power readings | "The office heater (switch.office_heater) has been on for 14 hours and is drawing 1800W. Everything else looks normal. Want me to turn it off?" |
| "Is everything okay?" | All sensors, device states, anomalies | "All good. 3 devices on (living room light, bedroom AC, kitchen fridge). No sensors showing unusual values. Front door is locked." |

**How it works:**

1. OpenClaw receives a diagnostic intent
2. Reads `tools/diagnostics.md` for instructions
3. Identifies which devices/areas are relevant to the question
4. Pulls data from HA API:
   - `/api/states` — current states of relevant entities
   - `/api/history/period/<start>` — recent history if needed (e.g., "how long has this been on?")
   - Weather integration data if temperature-related
5. Reasons over the collected data
6. Presents a diagnosis in plain language with a suggested action

**Skill file contents — what the prompt should instruct:**
```markdown
## Diagnostic Process

1. Identify the subject (which device, room, or system?)
2. Gather ALL relevant data:
   - The device's current state and attributes
   - Related sensors (temperature, humidity, power, motion)
   - Device history (how long has it been in this state?)
   - External factors (weather, time of day)
3. Look for mismatches:
   - AC is "on" but temperature is rising → check mode (fan vs cool)
   - Light is "on" but brightness is 0 → effectively off
   - Device is "unavailable" → check integration, network, power
4. Present findings as: observation → likely cause → suggested fix
5. Always offer to take action ("Want me to fix this?")
6. Don't overwhelm — lead with the most likely cause
```

---

## Feature 4: Proactive Monitor

**File:** `tools/proactive-monitor.md`
**Runs via:** Cron job (every 15 minutes)

**What it does:** Periodically checks sensor and device states, and messages the user when something looks off — without being asked.

**Example alerts:**

| Condition | Alert message |
|---|---|
| Living room 32°C, AC off, for 20+ min | "Your living room has been 32°C for 20 minutes and the AC is off. Want me to turn it on?" |
| Front door unlocked after 11 PM | "The front door has been unlocked since 9 PM. It's now 11:30 PM. Want me to lock it?" |
| Humidity above 80% | "Bedroom humidity is at 84%. The dehumidifier is off. Want me to turn it on?" |
| Device offline for 1+ hours | "The kitchen camera has been offline for 2 hours. You might want to check its connection." |
| All lights left on, no motion for 1+ hours | "All living room lights have been on for 2 hours but no motion detected. Want me to turn them off?" |

**How it works:**

1. Cron triggers OpenClaw every 15 minutes
2. OpenClaw reads `tools/proactive-monitor.md` for current alert rules
3. Pulls sensor data from HA API (`/api/states`)
4. Checks each rule against current state
5. If a rule triggers:
   - Check cooldown (don't re-alert the same thing within 2 hours)
   - Send message to user's platform (Discord/Teams/Feishu)
   - Log the alert in `tools/monitor-state.json`
6. If nothing triggers → silent, no message

**Alert state tracking** (`tools/monitor-state.json`):
```json
{
  "last_alerts": {
    "high_temp_living_room": "2026-03-30T22:15:00Z",
    "door_unlocked_late": "2026-03-30T23:30:00Z"
  },
  "cooldown_hours": 2
}
```

**Skill file contents — what the prompt should instruct:**
```markdown
## Monitoring Rules

Check these conditions every run. Only alert if:
- The condition has been true for the specified duration (not momentary spikes)
- No alert was sent for this condition in the last 2 hours
- It's not during quiet hours (midnight–7 AM) unless it's a security issue

### Temperature
- Room temp > 30°C and AC is off for 15+ min → alert
- Room temp < 16°C and heater is off for 15+ min → alert

### Security
- Door unlocked after 11 PM → alert (ignore quiet hours for security)
- Camera offline for 1+ hours → alert

### Energy
- Any device on for 8+ hours with no interaction → alert
- All lights on in a room with no motion for 1+ hours → alert

### Humidity
- Humidity > 75% and dehumidifier available but off → alert

## Anti-Annoyance Rules
- Max 3 alerts per day (non-security)
- Security alerts have no cap
- If user dismisses an alert, don't re-alert for 6 hours
- Never alert about devices the user just manually turned on/off
```

---

## Feature 5: Scene Learner

**File:** `tools/scene-learner.md`
**Runs via:** Cron job (daily at 9 AM)
**Depends on:** `tools/command-log.jsonl`

**What it does:** Reads the command log, finds repeating patterns, and suggests automations to the user.

**The command log** (`tools/command-log.jsonl`):

Every time OpenClaw executes an action, it appends one line:

```jsonl
{"ts":"2026-03-30T22:30:00Z","user":"kelvin","action":"turn_off","entity":"light.living_room","source":"discord"}
{"ts":"2026-03-30T22:31:00Z","user":"kelvin","action":"set_temperature","entity":"climate.bedroom","data":{"temperature":22},"source":"discord"}
{"ts":"2026-03-30T22:32:00Z","user":"kelvin","action":"turn_on","entity":"switch.bedroom_lamp","source":"discord"}
{"ts":"2026-03-31T22:28:00Z","user":"kelvin","action":"turn_off","entity":"light.living_room","source":"discord"}
{"ts":"2026-03-31T22:30:00Z","user":"kelvin","action":"set_temperature","entity":"climate.bedroom","data":{"temperature":22},"source":"discord"}
{"ts":"2026-03-31T22:31:00Z","user":"kelvin","action":"turn_on","entity":"switch.bedroom_lamp","source":"discord"}
```

**How it works:**

1. Daily cron triggers OpenClaw at 9 AM
2. OpenClaw reads `tools/scene-learner.md` for instructions
3. Reads the last 7 days of `tools/command-log.jsonl`
4. Feeds the log to the LLM with the prompt: "Find repeating patterns — same actions, similar times, same user, 3+ occurrences"
5. If a pattern is found:
   - Message the user: "I noticed you [pattern description]. Want me to create an automation for that?"
   - If user agrees → follow `tools/automations/_guide.md` to create the HA automation
   - If user declines → log the declined pattern so it's not suggested again
6. If no patterns → silent, no message

**Pattern detection criteria:**
- Same set of actions (order doesn't matter)
- Within a similar time window (±30 minutes)
- At least 3 occurrences in 7 days
- Not already an existing automation

**Declined patterns tracking** (append to `tools/scene-learner-state.json`):
```json
{
  "declined_patterns": [
    {
      "actions": ["turn_off:light.living_room", "set_temperature:climate.bedroom"],
      "declined_at": "2026-03-30",
      "reason": "user said they only do this sometimes"
    }
  ],
  "last_analysis": "2026-03-30"
}
```

---

## Command Log — The Shared Dependency

**File:** `tools/command-log.jsonl`

This is the only new piece of "infrastructure" — an append-only JSONL file. Every skill that executes a device action appends to it.

**Log entry schema:**
```json
{
  "ts": "ISO 8601 timestamp",
  "user": "username",
  "action": "service name (turn_on, turn_off, set_temperature, etc.)",
  "entity": "entity_id",
  "data": {},
  "source": "discord | teams | feishu",
  "intent": "direct | scene | diagnostic | proactive"
}
```

**Implementation:** Add one instruction to the existing `tools/_common.md`:
> "After every successful HA service call, append a JSONL line to tools/command-log.jsonl with the action details."

**Retention:** Keep 30 days. The scene learner cron can trim entries older than 30 days at the end of each run.

---

## Implementation Order

| Phase | What | Effort | Dependencies |
|---|---|---|---|
| **1** | Command log (append to _common.md) | Small | None |
| **2** | Intent router (update CLAUDE.md + new skill file) | Small | None |
| **3** | Scene executor | Medium | Intent router, command log |
| **4** | Diagnostics | Medium | Intent router |
| **5** | Proactive monitor | Medium | Command log, cron setup |
| **6** | Scene learner | Medium | Command log (needs 7+ days of data), cron setup |

**Phase 1-2** can be done immediately.
**Phase 3-4** can be done in parallel after Phase 2.
**Phase 5** can be done anytime after Phase 1.
**Phase 6** must wait until the command log has at least a week of data.

---

## Success Criteria

The demo should show these "wow moments":

1. **User says "I'm leaving"** → OpenClaw executes 4-5 coordinated actions and confirms in one message
2. **User says "Why is it so hot?"** → OpenClaw gathers data from 3+ sources and gives a reasoned diagnosis
3. **OpenClaw proactively messages** about a door left unlocked — without being asked
4. **After a week, OpenClaw suggests** "I noticed you do X every night — want me to automate that?"
5. **User says "Make it cozy"** → OpenClaw interprets the vague intent differently based on current conditions (cold evening vs hot afternoon)

Each of these is impossible with Alexa/Google Home/HA automations alone. That's the point.
