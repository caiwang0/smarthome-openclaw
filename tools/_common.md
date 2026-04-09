# Common — ha-mcp Tool Reference

## How Device Control Works

All HA interaction goes through ha-mcp tools (MCP protocol, stdio).
No curl. No API routing. No ports to configure.

ha-mcp handles authentication internally via HOMEASSISTANT_TOKEN env var.

## Commonly Used Tools

### Search entities
```
Tool: ha_search_entities
  query: "<search term>"
```

### Get entity state
```
Tool: ha_get_state
  entity_id: "<entity_id>"
```

### Call a service (device control)
```
Tool: ha_call_service
  domain: "<domain>"
  service: "<service>"
  entity_id: "<entity_id>"
  data: { ... }
```

### List areas
```
Tool: ha_get_areas
```

### Config entries
```
Tool: ha_config_entries_get
```

### Find the right tool
When unsure which tool to use:
```
Tool: ha_search_tools
  query: "<what you want to do>"
```

## Network Info

- Home Assistant: `http://homeassistant.local:<HA_PORT>` (read `HA_PORT` from `.env`; default 8123)
- ha-mcp: stdio process (no port, no URL) — spawned by Claude Code or OpenClaw
- mDNS: `homeassistant.local` resolves to the Pi's IP on the LAN
