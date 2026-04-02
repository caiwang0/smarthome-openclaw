# Skill Evaluation Fixes — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement all 12 decisions from the skill evaluation to fix contradictions, reduce token bloat, standardize API usage, and improve portability of the OpenClaw skill files.

**Architecture:** All changes are to Markdown documentation files and `.gitignore`. No code changes. The core pattern: CLAUDE.md becomes lean (behavioral rules only), rarely-used content moves to dedicated skill files in `tools/`, device files standardize on SmartHub API with placeholder entity IDs.

**Tech Stack:** Markdown, Git

---

### Task 1: Fix URL Formatting Contradiction

TOOLS.md says "send raw URLs" for Discord; CLAUDE.md says "always use markdown links." Decision: always markdown links.

**Files:**
- Modify: `TOOLS.md:67` (OAuth URL guidance)
- Modify: `CLAUDE.md:298` (already correct — verify only)

- [ ] **Step 1: Update TOOLS.md OAuth URL guidance**

In `TOOLS.md`, replace lines 66-69:

```
- **Send the raw URL on its own line** so Discord auto-links it. Do NOT use markdown `[text](url)` format — Discord doesn't render those as clickable in bot messages. Just paste the URL directly.
```

With:

```
- **Always send URLs as markdown hyperlinks:** `[Authorize <integration name>](extracted_url)`. Never paste raw URLs.
```

- [ ] **Step 2: Verify CLAUDE.md is consistent**

CLAUDE.md:332-338 already says "NEVER send a raw URL" and "Always wrap it as `[Short descriptive text](url)`." No change needed — just confirm it matches.

- [ ] **Step 3: Commit**

```bash
git add TOOLS.md
git commit -m "fix: resolve URL formatting contradiction — always use markdown links"
```

---

### Task 2: Standardize API Path — SmartHub for Device Control

Device files should use SmartHub API (`localhost:${API_PORT}/api/services/...`) for device control. The AC and cooker files currently use HA Direct API (`localhost:8123` with Bearer token). The TV file already uses SmartHub API — use it as the model.

**Files:**
- Modify: `tools/xiaomi-home/ma8-ac.md` (full rewrite of Commands section)
- Modify: `tools/xiaomi-home/p1v2-cooker.md` (full rewrite of Commands section)
- Modify: `tools/_common.md` (add API routing rule)

- [ ] **Step 1: Add API routing rule to `_common.md`**

Insert this section between line 7 (end of the API_PORT block quote) and line 9 (`## SmartHub API`), so it appears right after the title/setup and before the first API section:

```markdown
## API Routing Rule

- **Device control** (turn_on, turn_off, set_temperature, etc.) → **SmartHub API** (`http://localhost:${API_PORT}/api/services/...`). No auth header needed.
- **Config operations** (automations, integrations, area registry, config entries) → **HA Direct API** (`http://localhost:8123/api/...`). Requires `Authorization: Bearer $HA_TOKEN` header.

Always read `API_PORT` from `.env` before making SmartHub API calls. Never hardcode port 3001.
```

- [ ] **Step 2: Rewrite `ma8-ac.md` Commands section**

Replace the entire Commands section (lines 14-32) with SmartHub API pattern. Replace hardcoded entity IDs with `<entity_id>` placeholders:

```markdown
## Commands

> Read the API port first: `API_PORT=$(grep API_PORT .env | cut -d= -f2)`

### Power
```bash
# Turn on
curl -s -X POST http://localhost:${API_PORT}/api/services/climate/turn_on \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "<entity_id>"}'

# Turn off
curl -s -X POST http://localhost:${API_PORT}/api/services/climate/turn_off \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "<entity_id>"}'
```

### Set temperature and mode
```bash
curl -s -X POST http://localhost:${API_PORT}/api/services/climate/set_temperature \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "<entity_id>", "temperature": 24, "hvac_mode": "cool"}'
```

### Set HVAC mode
```bash
# Modes: off, cool, heat, heat_cool, auto, dry, fan_only
curl -s -X POST http://localhost:${API_PORT}/api/services/climate/set_hvac_mode \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "<entity_id>", "hvac_mode": "cool"}'
```

### Fan mode
```bash
curl -s -X POST http://localhost:${API_PORT}/api/services/select/select_option \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "<fan_mode_select_entity>", "option": "<mode_value>"}'
```
Look up available options from the entity's attributes via `/api/devices`.

### Horizontal swing
```bash
# Toggle horizontal swing on/off
curl -s -X POST http://localhost:${API_PORT}/api/services/switch/turn_on \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "<horizontal_swing_entity>"}'
```

### Child lock (physical controls lock)
```bash
# Lock
curl -s -X POST http://localhost:${API_PORT}/api/services/switch/turn_on \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "<physical_controls_locked_entity>"}'

# Unlock
curl -s -X POST http://localhost:${API_PORT}/api/services/switch/turn_off \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "<physical_controls_locked_entity>"}'
```

### Delay timer
```bash
# Enable delay
curl -s -X POST http://localhost:${API_PORT}/api/services/switch/turn_on \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "<delay_switch_entity>"}'

# Set delay time (minutes)
curl -s -X POST http://localhost:${API_PORT}/api/services/number/set_value \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "<delay_time_entity>", "value": 30}'
```

### Indicator light
```bash
curl -s -X POST http://localhost:${API_PORT}/api/services/light/turn_off \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "<indicator_light_entity>"}'
```
```

- [ ] **Step 3: Update `ma8-ac.md` Device Info and Key Entities**

Replace the Device Info section (lines 3-10) to use placeholder for primary entity:

```markdown
## Device Info

- **Name:** MA8 Air Conditioner
- **Type:** `climate` + switches/sensors
- **Model:** MA8
- **Integration:** Xiaomi Home (`xiaomi_home`)
- **Primary Entity:** Look up via `/api/devices` — pattern: `climate.xiaomi_*_ma8`
```

Replace the Key Entities table (lines 35-45) with entity patterns instead of hardcoded IDs:

```markdown
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
```

- [ ] **Step 4: Rewrite `p1v2-cooker.md` Commands and Device Info**

Replace the entire file with SmartHub API pattern and placeholder entity IDs:

```markdown
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
```

- [ ] **Step 5: Update `printer/office-printer.md` to use placeholder IP**

Replace the hardcoded IP `192.168.2.75` with a placeholder. Replace lines 3-5:

```markdown
- **Name:** Office Printer
- **Address:** `ipp://<PRINTER_IP>:631/ipp/print`
- **Toner:** Check via `lpstat -p office-printer`
```

Replace line 18 in the Setup section:

```markdown
sudo lpadmin -p office-printer -E -v ipp://<PRINTER_IP>:631/ipp/print -m everywhere
```

- [ ] **Step 6: Commit**

```bash
git add tools/_common.md tools/xiaomi-home/ma8-ac.md tools/xiaomi-home/p1v2-cooker.md tools/printer/office-printer.md
git commit -m "fix: standardize device files on SmartHub API with placeholder entity IDs"
```

---

### Task 3: Factor Integration Setup Out of CLAUDE.md

Move the entire "Adding Integrations" section (lines 69-327) from CLAUDE.md into `tools/integrations/_guide.md`. Replace with a 2-line pointer.

**Files:**
- Modify: `CLAUDE.md:69-327` (remove ~260 lines, replace with pointer)
- Create: `tools/integrations/_guide.md` (new file with extracted content)

- [ ] **Step 1: Create `tools/integrations/_guide.md`**

Create the file with the full integration setup content currently in CLAUDE.md lines 69-327. The content stays the same — it's just moving to a new home. Add a title header:

```markdown
# Integrations — Setup Guide

Every integration has its own setup flow with different steps and options. **Do NOT hardcode or assume what the options are.**

[... entire content of CLAUDE.md lines 72-327 goes here unchanged ...]
```

One change within the moved content: the OAuth URL line (currently CLAUDE.md:298) should match the new unified rule:

```
- **Always send URLs as markdown hyperlinks:** `[Authorize <integration name>](extracted_url)`. Never paste raw URLs.
```

- [ ] **Step 2: Replace CLAUDE.md integration section with pointer**

Replace CLAUDE.md lines 69-327 with:

```markdown
## Adding Integrations

When the user asks to add an integration (Xiaomi, Philips Hue, Broadlink, etc.), read `tools/integrations/_guide.md` for the full setup process. It covers HACS installation, config flows, OAuth handling, and error recovery.
```

- [ ] **Step 3: Commit**

```bash
mkdir -p tools/integrations
git add tools/integrations/_guide.md CLAUDE.md
git commit -m "refactor: move integration setup guide from CLAUDE.md to tools/integrations/_guide.md"
```

---

### Task 4: Remove Automation Duplication from CLAUDE.md

The automation trigger table and workflow in CLAUDE.md (lines 38-67) duplicates `_guide.md`. Replace with a pointer.

**Files:**
- Modify: `CLAUDE.md:38-67` (replace ~30 lines with 3-line pointer)

- [ ] **Step 1: Replace CLAUDE.md automation section**

Replace CLAUDE.md lines 38-67 (the "Creating Automations" section) with:

```markdown
## Creating Automations

When the user asks for an automation, read `tools/automations/_guide.md` and follow it step by step. It has the full workflow, required details checklist, JSON schema, and templates.

**Never create an automation without the user's explicit approval.**
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "refactor: deduplicate automation workflow — single source of truth in _guide.md"
```

---

### Task 5: Create `tools/_errors.md` — Error Handling Guide

**Files:**
- Create: `tools/_errors.md`

- [ ] **Step 1: Create `tools/_errors.md`**

```markdown
# Error Handling — Runtime Troubleshooting

## SmartHub API Errors

| HTTP Status | Meaning | Action |
|-------------|---------|--------|
| **503** | HA not connected | Check `docker ps`. If homeassistant is not running: `docker compose up -d`. If running, check logs: `docker logs homeassistant --tail 20` |
| **404** | Entity not found | Entity ID is wrong. Look up correct ID via `/api/devices`. Never guess entity IDs. |
| **400** | Service not found | Check domain/service spelling. Common services: `turn_on`, `turn_off`, `toggle` (switch only). See `_services.md` for full list. |
| **502** | HA service call failed | Check `docker logs homeassistant --tail 20` for details. May be a transient error — retry once. |

## Entity States

| State | Meaning | Action |
|-------|---------|--------|
| `unavailable` | Device offline or connection dropped | **Try the command anyway** — many devices (especially Xiaomi TV via DLNA) show unavailable but still respond. If the command fails, tell the user the device may be powered off. |
| `unknown` | HA hasn't received state yet | Device may still be initializing after restart. Wait 30-60 seconds, then retry. |

## Home Assistant Issues

| Symptom | Likely Cause | Action |
|---------|-------------|--------|
| All devices unavailable | HA restarted or integration crashed | Check `docker logs homeassistant --tail 50`. Try reloading the integration: `curl -s -X POST http://localhost:8123/api/config/config_entries/entry/<entry_id>/reload -H "Authorization: Bearer $HA_TOKEN"` |
| API timeout | Network issue or HA overloaded | Verify HA is running: `curl -s http://localhost:8123/api/`. Check `.env` has correct `HA_URL`. |
| Token rejected (401) | Token expired or invalid | Have user create a new long-lived access token in HA UI and update `.env`. |
| Port conflict | Another service using the port | Run `ss -tlnp \| grep ':<port> '` to find the conflict. See `tools/setup.md` Step 3b for resolution. |

## Recovery Steps

**Quick restart (fixes most transient issues):**
```bash
docker compose restart
API_PORT=$(grep API_PORT .env | cut -d= -f2)
# Wait for API to come back
for i in $(seq 1 15); do curl -s http://localhost:${API_PORT}/api/health 2>/dev/null | grep -q "ok" && break; sleep 2; done
```

**Reload a specific integration:**
```bash
HA_TOKEN=$(grep HA_TOKEN .env | cut -d= -f2)
# Find the config entry ID for the integration
curl -s http://localhost:8123/api/config/config_entries/entry \
  -H "Authorization: Bearer $HA_TOKEN" | python3 -c "
import json, sys
entries = json.load(sys.stdin)
for e in entries:
    if e['domain'] == '<integration_domain>':
        print(f\"Entry ID: {e['entry_id']} — {e['title']} (state: {e['state']})\")"

# Reload it
curl -s -X POST http://localhost:8123/api/config/config_entries/entry/<entry_id>/reload \
  -H "Authorization: Bearer $HA_TOKEN"
```
```

- [ ] **Step 2: Commit**

```bash
git add tools/_errors.md
git commit -m "feat: add runtime error handling guide"
```

---

### Task 6: Create `tools/_services.md` — Per-Domain Services Reference

**Files:**
- Create: `tools/_services.md`

- [ ] **Step 1: Create `tools/_services.md`**

```markdown
# Services by Domain — Quick Reference

> Use the SmartHub API for all device control: `http://localhost:${API_PORT}/api/services/<domain>/<service>`

## light

| Service | Data fields | Notes |
|---------|------------|-------|
| `turn_on` | `brightness` (0-255), `color_temp` (mireds), `rgb_color` ([r,g,b]) | All data fields optional |
| `turn_off` | — | |
| `toggle` | — | |

## switch

| Service | Data fields | Notes |
|---------|------------|-------|
| `turn_on` | — | |
| `turn_off` | — | |
| `toggle` | — | |

## climate

| Service | Data fields | Notes |
|---------|------------|-------|
| `turn_on` | — | |
| `turn_off` | — | |
| `set_temperature` | `temperature`, `hvac_mode` (optional) | |
| `set_hvac_mode` | `hvac_mode`: `off`, `cool`, `heat`, `heat_cool`, `auto`, `dry`, `fan_only` | States ARE HVAC modes, not on/off |
| `set_fan_mode` | `fan_mode` | Values are integration-specific |
| `set_swing_mode` | `swing_mode` | Values are integration-specific |

## media_player

| Service | Data fields | Notes |
|---------|------------|-------|
| `turn_on` | — | May not work if device disconnects Wi-Fi in standby |
| `turn_off` | — | |
| `volume_up` | — | |
| `volume_down` | — | |
| `volume_set` | `volume_level` (0.0 to 1.0) | |
| `volume_mute` | `is_volume_muted` (true/false) | |
| `media_play` | — | |
| `media_pause` | — | |
| `media_stop` | — | |
| `media_next_track` | — | |
| `media_previous_track` | — | |
| `select_source` | `source` | Check entity attributes for available sources |

## select

| Service | Data fields | Notes |
|---------|------------|-------|
| `select_option` | `option` | Check entity attributes for available options |

## number

| Service | Data fields | Notes |
|---------|------------|-------|
| `set_value` | `value` | Check entity attributes for min/max/step |

## button

| Service | Data fields | Notes |
|---------|------------|-------|
| `press` | — | One-shot action, no state |

## automation

| Service | Data fields | Notes |
|---------|------------|-------|
| `turn_on` | — | Enable an automation |
| `turn_off` | — | Disable an automation |
| `trigger` | — | Manually fire an automation |
| `reload` | — | Reload all automations from YAML |

## Brightness Conversion

Brightness in HA is 0-255, not 0-100%. To convert from percentage: `brightness = percentage × 2.55`

| User says | brightness value |
|-----------|-----------------|
| 25% | 64 |
| 50% | 128 |
| 75% | 191 |
| 100% | 255 |
```

- [ ] **Step 2: Commit**

```bash
git add tools/_services.md
git commit -m "feat: add per-domain services reference"
```

---

### Task 7: Split Automation Guide — Workflow vs Reference

Split `_guide.md` (685 lines) into a lean workflow (~200 lines) and a reference file (~485 lines).

**Files:**
- Modify: `tools/automations/_guide.md` (keep workflow, checklist, per-domain quick tables, recording format)
- Create: `tools/automations/_reference.md` (full JSON schema, all trigger/condition/action type examples, templates)

- [ ] **Step 1: Create `tools/automations/_reference.md`**

Move the following sections from `_guide.md` into `_reference.md`:
- "Automation JSON Schema" (lines 79-101)
- "Trigger Types" (lines 170-338) — all the detailed JSON examples for every trigger type
- "Condition Types" (lines 340-399)
- "Action Types" (lines 401-475)
- "Common Automation Templates" (lines 477-605)

The new file starts with:

```markdown
# Automations — JSON Reference

> This file contains the full JSON schema, trigger/condition/action type examples, and automation templates.
> For the creation workflow and required details checklist, see `_guide.md`.

[... moved sections from _guide.md ...]
```

- [ ] **Step 2: Trim `_guide.md` and add pointer**

`_guide.md` keeps:
- Workflow (lines 1-17)
- REST API Reference (lines 19-76)
- Required Details Checklist (lines 105-167) — this is the best part, stays in the workflow
- Per-Domain Trigger Reference (lines 607-654) — quick lookup tables
- Recording Created Automations (lines 656-673)
- Important Notes (lines 677-685)

Add a pointer after the Required Details Checklist:

```markdown
For the full JSON schema, all trigger/condition/action type examples with code, and common automation templates, read `_reference.md`.
```

- [ ] **Step 3: Commit**

```bash
git add tools/automations/_guide.md tools/automations/_reference.md
git commit -m "refactor: split automation guide into workflow (_guide.md) and reference (_reference.md)"
```

---

### Task 8: Update TOOLS.md — Quick Reference + Replace Integration Section

Add the new files to the routing table. Replace the 67-line "Adding New Integrations" section (lines 21-88) with a pointer to `tools/integrations/_guide.md` — that section now duplicates the new guide AND has a broken reference to CLAUDE.md (which no longer contains integration setup).

**Files:**
- Modify: `TOOLS.md:6-14` (Quick Reference table)
- Modify: `TOOLS.md:21-88` (replace integration section with pointer)

- [ ] **Step 1: Update Quick Reference table**

Replace the table at TOOLS.md lines 6-14 with:

```markdown
| Skill File | What It Covers |
|------------|----------------|
| [tools/_common.md](tools/_common.md) | SmartHub API, HA Direct API, auth tokens, network info, API routing rule |
| [tools/_errors.md](tools/_errors.md) | Runtime error handling — HTTP errors, entity states, recovery steps |
| [tools/_services.md](tools/_services.md) | Per-domain service reference (light, climate, media_player, etc.) |
| [tools/integrations/_guide.md](tools/integrations/_guide.md) | Integration setup — HACS, config flows, OAuth, error handling |
| [tools/xiaomi-home/_integration.md](tools/xiaomi-home/_integration.md) | Xiaomi Home setup, OAuth, cloud regions, shared quirks |
| [tools/xiaomi-home/tv.md](tools/xiaomi-home/tv.md) | Xiaomi TV commands and quirks |
| [tools/xiaomi-home/ma8-ac.md](tools/xiaomi-home/ma8-ac.md) | MA8 Air Conditioner commands and quirks |
| [tools/xiaomi-home/p1v2-cooker.md](tools/xiaomi-home/p1v2-cooker.md) | P1V2 Smart Cooker commands and quirks |
| [tools/printer/office-printer.md](tools/printer/office-printer.md) | Office printer setup and print commands |
| [tools/automations/_guide.md](tools/automations/_guide.md) | **Automation creation** — workflow, required details checklist, per-domain triggers |
| [tools/automations/_reference.md](tools/automations/_reference.md) | Automation JSON schema, all trigger/condition/action types, templates |
```

- [ ] **Step 2: Replace integration section with pointer**

Replace TOOLS.md lines 21-88 (the entire "Adding New Integrations (Config Flows)" section, including the config flow steps, form handling, OAuth guidance, and stale flow cleanup) with:

```markdown
## Adding New Integrations

For the full integration setup process (HACS, config flows, OAuth, form handling, error recovery), read `tools/integrations/_guide.md`.
```

The Skill Auto-Generation section (starts after line 88) stays — that's different content.

- [ ] **Step 3: Commit**

```bash
git add TOOLS.md
git commit -m "docs: update TOOLS.md — new quick reference table, replace integration section with pointer"
```

---

### Task 9: Update .gitignore — Automation Records

Gitignore instance-specific automation records but keep the guide and reference files.

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: Add automation records to .gitignore**

Append to `.gitignore`:

```
# Instance-specific automation records (auto-generated per user)
tools/automations/*.md
!tools/automations/_guide.md
!tools/automations/_reference.md
```

- [ ] **Step 2: Remove tracked automation records from git index**

The files are already tracked, so we need to remove them from git's index without deleting the actual files:

```bash
git rm --cached tools/automations/tv_off_334pm.md tools/automations/tv_off_1529_sgt.md
```

- [ ] **Step 3: Commit**

```bash
git add .gitignore
git commit -m "chore: gitignore instance-specific automation records"
```

---

### Task 10: Update CLAUDE.md "How to Interact" Section

Now that we have `_errors.md` and `_services.md`, update the instruction to reference them.

**Files:**
- Modify: `CLAUDE.md:27-36` (the "How to Interact with Home Assistant" section)

- [ ] **Step 1: Update the section**

Replace CLAUDE.md lines 27-36 with:

```markdown
## How to Interact with Home Assistant

Device commands, API patterns, and device-specific knowledge are organized in the `tools/` folder.

**Before controlling any device:**
1. Read `tools/_common.md` for API patterns, auth tokens, and the API routing rule
2. Read the device's skill file (e.g., `tools/xiaomi-home/tv.md`) for specific commands and quirks
3. If unsure which device file to use, check `TOOLS.md` for the Quick Reference table
4. If unsure which services are available for a domain, check `tools/_services.md`
5. If a command fails, check `tools/_errors.md` for troubleshooting

**Before creating an automation**, read `tools/automations/_guide.md` for the full workflow. For JSON schema and all trigger/condition/action types, read `tools/automations/_reference.md`.

**Before adding an integration**, read `tools/integrations/_guide.md` for the full setup process.

**After completing any action**, follow the Skill Auto-Generation rules in `TOOLS.md` to keep skill files up to date.
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md to reference new skill files"
```

---

### Task 11: Update Skill Auto-Generation Template in TOOLS.md

The device skill template in TOOLS.md should reflect the new conventions: SmartHub API, placeholder entity IDs, entity pattern table.

**Files:**
- Modify: `TOOLS.md:126-147` (skill file template)

- [ ] **Step 1: Update the template**

Replace TOOLS.md lines 126-147 with:

```markdown
### Skill file template for new devices

```markdown
# <Device Name>

## Device Info

- **Name:** <name>
- **Type:** `<domain>` (<sub-type if relevant>)
- **Model:** `<model>`
- **Integration:** <Integration Name> (`<integration_domain>`)
- **Primary Entity:** Look up via `/api/devices` — pattern: `<domain>.xiaomi_*_<model_slug>`

## Commands

> Read the API port first: `API_PORT=$(grep API_PORT .env | cut -d= -f2)`

<curl examples using http://localhost:${API_PORT}/api/services/... with placeholder entity IDs>

### Key entities

| Purpose | Entity pattern | Domain |
|---------|---------------|--------|
| <description> | `<domain>.xiaomi_*_<model>_<suffix_pattern>` | <domain> |

## Quirks

- None known yet.
```
```

- [ ] **Step 2: Commit**

```bash
git add TOOLS.md
git commit -m "docs: update device skill template with SmartHub API and placeholder conventions"
```

---

### Task 12: Final Verification

- [ ] **Step 1: Verify CLAUDE.md line count reduction**

```bash
wc -l CLAUDE.md
# Should be ~80-100 lines (down from 368)
```

- [ ] **Step 2: Verify no broken internal references**

```bash
# Check that all referenced files exist
grep -oP 'tools/[a-zA-Z0-9/_.-]+\.md' CLAUDE.md TOOLS.md | sort -u | while read f; do
  [ -f "$f" ] || echo "MISSING: $f"
done
```

- [ ] **Step 3: Verify no hardcoded entity IDs remain in template files**

```bash
# Should return nothing — gitignored automation records and _reference.md examples are excluded
grep -rn 'xiaomi_cn_[0-9]' tools/ | grep -v '_reference.md' | grep -v 'automations/tv_off'
# Should return nothing
```

- [ ] **Step 4: Verify .gitignore works**

```bash
git status tools/automations/
# tv_off_334pm.md and tv_off_1529_sgt.md should NOT appear as tracked
```

- [ ] **Step 5: Final commit (if any verification fixes needed)**

```bash
git add -A
git commit -m "chore: verification fixes"
```
