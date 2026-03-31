# TOOLS.md — Smart Home Skill Router

This file is the entry point for all device and service knowledge. Detailed commands, capabilities, and quirks live in the `tools/` folder.

## Quick Reference

| Skill File | What It Covers |
|------------|----------------|
| [tools/_common.md](tools/_common.md) | SmartHub API, HA Direct API, auth tokens, network info |
| [tools/xiaomi-home/_integration.md](tools/xiaomi-home/_integration.md) | Xiaomi Home setup, OAuth, cloud regions, shared quirks |
| [tools/xiaomi-home/tv.md](tools/xiaomi-home/tv.md) | Xiaomi TV commands and quirks |
| [tools/printer/office-printer.md](tools/printer/office-printer.md) | Office printer setup and print commands |
| [tools/automations/_guide.md](tools/automations/_guide.md) | **Automation creation** — HA API, trigger types, templates, per-domain reference |

**Before controlling a device**, read its skill file for the correct entity ID, commands, and known quirks.

**For general API patterns** (listing devices, calling services, managing areas), read `tools/_common.md`.

**For creating automations**, read `tools/automations/_guide.md` — it has the full workflow, JSON schema, and templates.

---

## Adding New Integrations (Config Flows)

**Step 0 — ALWAYS check if the integration exists first.** See CLAUDE.md "Step 0 — Check if the integration is available" for the full process. If the integration is not installed (e.g., `xiaomi_home` needs HACS), handle HACS installation first before proceeding.

**Then offer BOTH options:**

> **Option 1 — Do it yourself in the HA UI:** [Open HA Integrations](http://localhost:8123/config/integrations/dashboard) → click "Add Integration" → search for [integration name]. Let me know when you're done and I'll check what devices were added.
>
> **Option 2 — I'll guide you step by step.** Here's the first step:

Then immediately show the first form step below. This way the user sees both options at once and can pick either without waiting.

**For guided setup:**

Every integration has different steps and options. NEVER hardcode or assume values. Read the actual `data_schema` from each step and present ALL options to the user.

**Step 1: Start a config flow**
```bash
HA_TOKEN=$(grep HA_TOKEN .env | cut -d= -f2)

curl -s -X POST http://localhost:8123/api/config/config_entries/flow \
  -H "Authorization: Bearer $HA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"handler": "<integration_domain>"}'
```

**Step 2: For EVERY step, read the response and act based on `type`:**

| `type` | Action |
|--------|--------|
| `form` | Read `data_schema`, present ALL fields to user, ask for their choices, then submit |
| `external` / `progress` | Extract OAuth URL, send to user as clickable link, wait for them to confirm |
| `abort` | Tell user the reason. If `already_in_progress`, offer to clear stale flows |
| `create_entry` | Done! Run the post-integration skill generation (see below), then show what devices were added |

**For `form` steps — present every field:**
- `select` → show all options as a numbered list, ask user to pick
- `multi_select` → show all options, ask user to pick one or more
- `boolean` → ask yes/no, show the default
- `string` / `integer` → ask user to type a value
- **NEVER auto-fill fields without asking the user**, even if there's a default

**For OAuth steps:**
- Extract the raw URL from the response (may be in `description_placeholders` as an HTML `<a href="...">` tag — extract the `href` value)
- **Send the raw URL on its own line** so Discord auto-links it. Do NOT use markdown `[text](url)` format — Discord doesn't render those as clickable in bot messages. Just paste the URL directly.
- Tell user: "Click the link, log in, authorize, and let me know when done."
- If `homeassistant.local` doesn't load, tell them to add a hosts entry: `the Pi's IP address homeassistant.local`
- After user confirms, poll the flow to check if it advanced

**Step 3: Submit user's choices**
```bash
curl -s -X POST http://localhost:8123/api/config/config_entries/flow/<flow_id> \
  -H "Authorization: Bearer $HA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"field_name": "user_choice", ...}'
```

**Step 4: Repeat until `type` = `create_entry`**

**Clearing stale flows (if `already_in_progress`):**
```bash
curl -s -X DELETE http://localhost:8123/api/config/config_entries/flow/<flow_id> \
  -H "Authorization: Bearer $HA_TOKEN"
```

---

## Skill Auto-Generation

You maintain the `tools/` folder automatically. Follow these rules:

### After a new integration completes (`create_entry`)

1. Query `API_PORT=$(grep API_PORT .env | cut -d= -f2); curl -s http://localhost:${API_PORT}/api/devices` to discover new devices
2. Determine the integration domain (e.g., `xiaomi_home`, `hue`, `broadlink`)
3. If `tools/<integration>/` doesn't exist, create it
4. If `tools/<integration>/_integration.md` doesn't exist, create it with:
   - Integration name and domain
   - Setup notes (OAuth? Local? Cloud region?)
   - Any shared quirks discovered during setup
   - A Devices table listing all devices in this integration
5. For each new device, create `tools/<integration>/<device-name>.md` with:
   - Device info (name, device ID, type, model, primary entity ID)
   - Commands section with curl examples for all applicable services based on the device's domain (use the patterns from `tools/_common.md`)
   - An empty Quirks section
6. Update the Quick Reference table at the top of this file (TOOLS.md) with the new skill files
7. Update the Devices table in `_integration.md`

### After running a novel command on a device

If you execute a command pattern that is NOT already documented in the device's skill file:
1. Read the device's skill file
2. Append the new command under the appropriate section (or create a new section)
3. If you encountered unexpected behavior, add it to the Quirks section

### After discovering a quirk

If a device behaves unexpectedly (e.g., returns "unavailable" but still responds, requires a specific parameter format, has a timing constraint):
1. Add the quirk to the device's skill file under `## Quirks`
2. If the quirk affects all devices in the integration, also add it to `_integration.md` under `## Shared Quirks`

### Skill file template for new devices

```markdown
# <Device Name>

## Device Info

- **Name:** <name>
- **Device ID:** `<device_id>`
- **Type:** `<domain>` (<sub-type if relevant>)
- **Model:** `<model>`
- **Integration:** <Integration Name> (`<domain>`)
- **Primary Entity:** `<entity_id>`

## Commands

> Read the API port first: `API_PORT=$(grep API_PORT .env | cut -d= -f2)`

<curl examples using http://localhost:${API_PORT}/api/services/...>

## Quirks

- None known yet.
```
