# Common — ha-mcp Tool Reference

## How Device Control Works

All HA interaction goes through ha-mcp tools (MCP protocol, stdio).
No curl. No API routing. No ports to configure.

ha-mcp handles authentication internally via HOMEASSISTANT_TOKEN env var.

## Network Info

- macOS host: only for `install.sh`, VirtualBox, and SSH bootstrap. Do not assume HA is running here.
- Linux guest: Home Assistant, Docker, Avahi, and `homeassistant.local` live here. Read `HA_PORT` from `.env`; default 8123.
- browser machine: open the dashboard or OAuth links here. On the LAN, use `http://homeassistant.local:<HA_PORT>`.
- ha-mcp: stdio process (no port, no URL) — spawned by Claude Code or OpenClaw
