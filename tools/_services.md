# Services by Domain — Quirks & Patterns

> For the full per-domain service catalog, call `ha_list_services` (e.g., `ha_list_services(domain="light")`). This file keeps only the SmartHub-specific quirks and conversion rules the LLM cannot derive from tool schemas.

## Quirks & Patterns

- **`climate.set_hvac_mode`** — States ARE HVAC modes, not on/off. The `state` of a `climate.*` entity is the current HVAC mode string (`off`, `cool`, `heat`, `heat_cool`, `auto`, `dry`, `fan_only`), not a boolean. Don't compare entity state to `"on"` or `"off"`.
- **`media_player.turn_on`** — May not work if device disconnects Wi-Fi in standby. If `turn_on` silently fails, the device is likely off-network; tell the user and suggest a physical power check instead of retrying.
- **`media_player.select_source`** — Check entity attributes for available sources. Read the `source_list` attribute from `ha_get_state` before calling — sources are per-device.
- **`select.select_option`** — Check entity attributes for available options. Read the `options` attribute from `ha_get_state` before calling.
- **`number.set_value`** — Check entity attributes for min/max/step. Read `min`, `max`, `step` attributes from `ha_get_state` before calling; setting a value outside the range can fail silently on some integrations.

## Brightness Conversion

Brightness in HA is 0-255, not 0-100%. To convert from percentage: `brightness = percentage × 2.55`

| User says | brightness value |
|-----------|-----------------|
| 25% | 64 |
| 50% | 128 |
| 75% | 191 |
| 100% | 255 |
