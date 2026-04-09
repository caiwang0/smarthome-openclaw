# Services by Domain — Quick Reference

> Use `ha_call_service` for all device control. For a full list of services for any domain, use `ha_list_services`.

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
