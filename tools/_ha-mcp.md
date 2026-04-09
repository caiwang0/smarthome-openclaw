# ha-mcp — Tool Reference

Quick reference for the most-used ha-mcp tools. Full list: use `ha_search_tools`.

## Device Control

| Task | Tool | Key params |
|---|---|---|
| Turn on/off | `ha_call_service` | domain, service, entity_id |
| Check state | `ha_get_state` | entity_id |
| Find entities | `ha_search_entities` | query |
| List areas | `ha_get_areas` | — |

## Automation Management

| Task | Tool | Key params |
|---|---|---|
| Create/update | `ha_config_set_automation` | config dict |
| Delete | `ha_config_delete_automation` | automation_id |
| Get config | `ha_config_get_automation` | automation_id |
| Debug traces | `ha_get_automation_traces` | automation_id |

## Integration Management

| Task | Tool | Key params |
|---|---|---|
| List config entries | `ha_config_entries_get` | — |
| Start config flow | `ha_config_entries_flow` | handler |
| HACS search | `ha_hacs_search` | query |
| HACS download | `ha_hacs_download` | repository |

## Helpers

| Task | Tool | Key params |
|---|---|---|
| Create helper | `ha_create_helper` | type, name |
| List services | `ha_list_services` | domain (optional) |

## Tool Search

When you don't know the right tool:
```
Tool: ha_search_tools
  query: "<what you want to do>"
```
