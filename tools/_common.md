# Common — ha-mcp Tool Reference

## How Device Control Works

All HA interaction goes through ha-mcp tools (MCP protocol, stdio).
No curl. No API routing. No ports to configure.

ha-mcp handles authentication internally via HOMEASSISTANT_TOKEN env var.

## Network Info

- Home Assistant: `http://homeassistant.local:<HA_PORT>` (read `HA_PORT` from `.env`; default 8123)
- ha-mcp: stdio process (no port, no URL) — spawned by Claude Code or OpenClaw
- mDNS: `homeassistant.local` resolves to the Pi's IP on the LAN
