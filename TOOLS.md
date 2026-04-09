# TOOLS.md — Smart Home Skill Router

This file is the entry point for all device and service knowledge. Detailed commands, capabilities, and quirks live in the `tools/` folder.

## Quick Reference

| Skill File | What It Covers |
|------------|----------------|
| [tools/_common.md](tools/_common.md) | ha-mcp tool patterns, network info |
| [tools/_errors.md](tools/_errors.md) | Runtime error handling — HTTP errors, entity states, recovery steps |
| [tools/_services.md](tools/_services.md) | Per-domain service reference (light, climate, media_player, etc.) |
| [tools/_ha-mcp.md](tools/_ha-mcp.md) | ha-mcp tool quick reference — device control, automations, integrations, helpers |
| [tools/integrations/_guide.md](tools/integrations/_guide.md) | Integration setup — HACS, config flows, OAuth, error handling |
| [tools/xiaomi-home/_integration.md](tools/xiaomi-home/_integration.md) | Xiaomi Home setup, OAuth, cloud regions, shared quirks |
| [tools/xiaomi-home/tv.md](tools/xiaomi-home/tv.md) | Xiaomi TV commands and quirks |
| [tools/xiaomi-home/ma8-ac.md](tools/xiaomi-home/ma8-ac.md) | MA8 Air Conditioner commands and quirks |
| [tools/xiaomi-home/p1v2-cooker.md](tools/xiaomi-home/p1v2-cooker.md) | P1V2 Smart Cooker commands and quirks |
| [tools/printer/office-printer.md](tools/printer/office-printer.md) | Office printer setup and print commands |
| [tools/automations/_guide.md](tools/automations/_guide.md) | **Automation creation** — workflow, required details checklist, per-domain triggers |
| [tools/automations/_reference.md](tools/automations/_reference.md) | Automation JSON schema, all trigger/condition/action types, templates |

**Before controlling a device**, read its skill file for the correct entity ID, commands, and known quirks.

**For ha-mcp tool patterns** (listing devices, calling services, managing areas), read `tools/_common.md`.

**For creating automations**, read `tools/automations/_guide.md` — it has the full workflow and checklist.

---

## Adding New Integrations

For the full integration setup process (HACS, config flows, OAuth, form handling, error recovery), read `tools/integrations/_guide.md`.

---

## Skill Auto-Generation

You maintain the `tools/` folder automatically. Follow these rules:

### After a new integration completes (`create_entry`)

1. Use `ha_search_entities` to discover new devices from the integration
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
- **Type:** `<domain>` (<sub-type if relevant>)
- **Model:** `<model>`
- **Integration:** <Integration Name> (`<integration_domain>`)
- **Primary Entity:** Look up via `ha_search_entities` — pattern: `<domain>.xiaomi_*_<model_slug>`

## Commands

<ha-mcp tool call examples using ha_call_service with placeholder entity IDs>

### Key entities

| Purpose | Entity pattern | Domain |
|---------|---------------|--------|
| <description> | `<domain>.xiaomi_*_<model>_<suffix_pattern>` | <domain> |

## Quirks

- None known yet.
```
