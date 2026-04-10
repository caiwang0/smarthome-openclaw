# Design: Replace SmartHub API with ha-mcp

**Date:** 2026-04-09
**Status:** Proposed
**Author:** Kelvin + OpenClaw

---

## Intent

**Goal:** Replace the custom SmartHub API server with ha-mcp (stock, unmodified) as the sole HA communication layer. Reduce maintenance burden, gain 87 structured tools, WebSocket state verification, and community-maintained HA integration — while adding structured approval gating for destructive operations.

**Priority ranking:**
1. Reliability — commands verified via WebSocket, not assumed successful
2. Safety — destructive operations gated through user approval on messaging platform
3. Simplicity — fewer components, fewer moving parts, less custom code
4. Latency — tool search ON to reduce context window size (beta users flagged response time)

**Decision boundaries:**
- ha-mcp is used stock. If something requires forking ha-mcp, reconsider the approach.
- Approval gating relies on OpenClaw's MCP client behavior. If OpenClaw doesn't support annotations or hooks, escalate — don't build a proxy.

**Stop rules:**
- If ha-mcp cannot reach HA on the Pi's Docker network, stop and investigate before continuing.
- If OpenClaw's ACPX/Claude Code bridge cannot connect to ha-mcp, stop and investigate the interim path.

**Out of scope:**
- Public response to data exfiltration / open source claims (marketing workstream)
- Local model support via Ollama (feature workstream)
- YAML-only export mode (feature workstream)
- Automation audit/attribution log (feature workstream)

---

## Architecture

```
User (any messaging platform)
    |
OpenClaw (bot framework + LLM orchestration)
    |-- Reads: CLAUDE.md, TOOLS.md, tools/*.md
    |-- Approval gating: checks MCP tool annotations
    |
    | MCP protocol (stdio)
    |
ha-mcp (stock, unmodified, 87 tools)
    |
    | REST + WebSocket
    |
Home Assistant (Docker)
```

Three components. No custom API server. No fork of ha-mcp.

### What stays
- OpenClaw as user-facing bot (messaging platforms, conversation, LLM)
- CLAUDE.md as agent behavior rules
- Skill files in `tools/` for device-specific knowledge
- Docker Compose for Home Assistant
- Install and setup flow (modified)

### What goes
- SmartHub API server (`api/` directory) — replaced entirely by ha-mcp
- `ha-client.ts`, `device-aggregator.ts`, all Elysia routes
- The Bun/Elysia Docker container
- `API_PORT` environment variable

### What's new
- ha-mcp installed via uvx, runs as stdio MCP server (pinned to v7.2.0)
- OpenClaw connects to ha-mcp via native MCP (when shipped) or Claude Code bridge (interim)
- Approval gating via OpenClaw annotation handling, hook fallback, and CLAUDE.md safety net

---

## ha-mcp Configuration

ha-mcp runs as a stdio process spawned by OpenClaw (or Claude Code in interim). No extra port, no HTTP server, no Docker container for ha-mcp.

### OpenClaw config (once native MCP ships)

```json
{
  "mcp": {
    "servers": {
      "ha-mcp": {
        "command": "uvx",
        "args": ["ha-mcp"],
        "env": {
          "HOMEASSISTANT_URL": "http://localhost:8123",
          "HOMEASSISTANT_TOKEN": "${HA_TOKEN}"
        }
      }
    }
  }
}
```

### Interim config (Claude Code bridge)

```json
// .claude/settings.json (project-level)
{
  "mcpServers": {
    "ha-mcp": {
      "command": "uvx",
      "args": ["ha-mcp"],
      "env": {
        "HOMEASSISTANT_URL": "http://localhost:8123",
        "HOMEASSISTANT_TOKEN": "${HA_TOKEN}"
      }
    }
  }
}
```

### ha-mcp settings

| Setting | Value | Rationale |
|---|---|---|
| `ENABLE_SKILLS` | `true` | HA best-practice knowledge (automation patterns, helper selection) — complements our device-specific skill files |
| `ENABLE_SKILLS_AS_TOOLS` | `true` | Guarantees skills are accessible even if OpenClaw's MCP client doesn't support the resources protocol |
| `ENABLE_TOOL_SEARCH` | `true` | Replaces 87 tool schemas with a BM25 search tool. Smaller context window → faster responses, lower token cost. LLM learns tool names after first use — extra search call is one-time per tool per conversation |
| `ENABLE_WEBSOCKET` | `true` | After calling a service, ha-mcp waits for WebSocket confirmation that the state actually changed. Bot reports real results, not assumed success |

---

## Approval Gating

Three layers, strongest to weakest:

### Layer 1: OpenClaw MCP annotation handling (primary)

Every ha-mcp tool carries annotations:

- `readOnlyHint: true` — safe, executes immediately
- `destructiveHint: true` — creates, modifies, or deletes data

When OpenClaw's native MCP client reads these annotations, it prompts the user before executing destructive tools. The user confirms via their messaging platform (button tap or text reply). Zero custom code.

### Layer 2: OpenClaw hook (contingent — research spike required)

**Status:** This layer cannot be implemented until OpenClaw documents its MCP hook interface. The `hooks` config section exists in `openclaw.json`, but the MCP-specific hook interface (`mcp-tool-before`) is not yet documented and may not exist.

**Research spike before implementation:**
1. Confirm with OpenClaw team whether `mcp-tool-before` (or equivalent) hook exists and its exact signature
2. Identify the messaging platform SDK call(s) needed to send a confirmation prompt to the user (Feishu API? Discord API? OpenClaw unified messaging API?)
3. Define timeout behavior: if the user never replies, does the hook exit 0 (allow), exit 1 (block), or timeout after N seconds?

**Conceptual design (not implementable yet):**

```json
{
  "hooks": {
    "mcp-tool-before": {
      "command": "python3 scripts/approval_gate.py",
      "args": ["${tool_name}", "${tool_annotations}"]
    }
  }
}
```

`scripts/approval_gate.py` would:
- Read tool name and annotations from args
- If `destructiveHint: true`: send confirmation message via messaging API
- If approved: exit 0 (tool executes)
- If rejected or timeout (30s default): exit 1 (tool blocked)

**Do NOT implement this layer until the research spike is complete.** Do not build a custom proxy. Rely on Layer 3 until OpenClaw adds hook support. `scripts/approval_gate.py` is NOT created during this migration — it is a future deliverable tracked separately.

### Layer 3: CLAUDE.md rules (safety net)

Existing rules stay as-is:

```
CRITICAL — Confirmation required for persistent changes:
- NEVER create, modify, or delete an automation without showing
  the user a summary first and waiting for their explicit "yes"
- NEVER add or remove an integration without user confirmation
```

Costs nothing. Already in place. Catches cases where layers 1 and 2 miss something.

### What's NOT gated (read operations)

These execute immediately, no confirmation:
- Searching entities (`ha_search_entities`)
- Checking device state (`ha_get_state`)
- Viewing automation config (`ha_config_get_automation`)
- Reading history/statistics (`ha_get_history`, `ha_get_statistics`)
- Listing areas, zones, helpers
- Viewing automation traces (`ha_get_automation_traces`)

### User experience

Regardless of which layer triggers it:

```
User: "Delete the AC automation"

Bot:  Delete Automation
      Name: AC off at 3am
      Triggers: Every day at 03:00
      Actions: Turn off climate.living_room

      Reply "yes" to confirm or "no" to cancel.

User: yes

Bot:  Done — automation "AC off at 3am" deleted.
```

### Security model

The approval is secure because:
- The AI runs on the Pi — it only has the bot API token
- The user confirms on their phone — their messaging session lives on a separate device
- The messaging platform (Feishu/Discord/Telegram) authenticates who sent the reply
- The AI cannot forge a user's approval because it doesn't control the user's device

---

## Repo Changes

### Files removed

```
api/                          # Entire SmartHub API server
  src/index.ts                # Elysia app entry, middleware, health endpoint
  src/ha-client.ts            # WebSocket connection to HA, callHAService()
  src/device-aggregator.ts    # Device listing, status logic, area aggregation
  src/types.ts                # TypeScript interfaces (HADevice, HAEntity, etc.)
  src/routes/
    devices.ts                # GET /api/devices — ha-mcp: ha_search_entities, ha_get_state
    areas.ts                  # GET /api/areas — ha-mcp: ha_get_areas
    services.ts               # POST /api/services/:domain/:service — ha-mcp: ha_call_service
    camera.ts                 # GET /api/camera/:entity_id/snapshot — ha-mcp: ha_get_state (camera proxy is HA-native, not needed in API layer)
    chat.ts                   # POST /api/chat — SSE proxy to OpenClaw. INTENTIONALLY DROPPED: chat goes through OpenClaw directly, not via SmartHub API
    xiaomi.ts                 # Xiaomi config_entries flow — ha-mcp: ha_config_entries_flow tools
  Dockerfile                  # Bun runtime Docker image
  package.json                # Elysia + home-assistant-js-websocket deps
  bun.lock                    # Dependency lock
  tsconfig.json               # TypeScript config
```

**Coverage confirmation:** All 6 route groups have ha-mcp equivalents except `chat.ts`, which is intentionally dropped (it proxies to OpenClaw, which is the caller — circular dependency removed). Camera snapshots are available via HA's native `/api/camera_proxy/<entity_id>` endpoint, which ha-mcp can access via `ha_call_service` or direct URL if needed.

### Files modified

| File | Change |
|---|---|
| `docker-compose.yml` | Remove `api` service (lines 14–26). Only `homeassistant` remains. |
| `.env.example` | Remove `API_PORT` line. Keep `HA_URL`, `HA_TOKEN`, `TZ`. |
| `CLAUDE.md` | See detailed CLAUDE.md changes below. |
| `TOOLS.md` | See detailed TOOLS.md changes below. |
| `tools/_common.md` | Biggest rewrite. Replace API routing rule, curl patterns, auth token instructions with ha-mcp tool reference guide. |
| `tools/_errors.md` | See detailed _errors.md changes below. |
| `tools/_services.md` | Simplify — point to `ha_list_services` tool instead of manual service list. |
| `tools/automations/_guide.md` | Replace manual JSON POST workflow with `ha_config_set_automation` / `ha_config_get_automation` tool calls. |
| `tools/automations/_reference.md` | Keep JSON schema (LLM needs it for config dict). Add header note: "To create/update automations, use `ha_config_set_automation` tool with this schema." |
| `tools/integrations/_guide.md` | See detailed integrations/_guide.md changes below. |
| Device skill files (`tools/xiaomi-home/*.md`, etc.) | Replace curl examples with ha-mcp tool call syntax. Device quirks unchanged. |
| `install.sh` | See detailed install.sh changes below. |
| `tools/setup.md` | See detailed setup.md changes below. |
| `README.md` | Update architecture diagram: remove "SmartHub API" box, show OpenClaw → ha-mcp → HA path. |

#### Detailed CLAUDE.md changes

| Location | Current | New |
|---|---|---|
| First-run check #3 (line 17) | `curl ... localhost:${API_PORT}/api/health` | `HOMEASSISTANT_TOKEN=$(grep HA_TOKEN .env \| cut -d= -f2) HOMEASSISTANT_URL=$(grep HA_URL .env \| cut -d= -f2) uvx ha-mcp@7.2.0 --smoke-test 2>/dev/null && echo "MCP_OK" \|\| echo "MCP_DOWN"` (see smoke-test section for fallback) |
| "How to Interact with HA" section | References `tools/_common.md` for API patterns, curl | Reference `tools/_common.md` for ha-mcp tool patterns. Remove all curl/API routing language. |
| Line 89: `/api/devices` reference | `"Always check /api/devices first if unsure"` | `"Always check via ha_search_entities first if unsure"` |
| Line 91: "API response" | `"read the form fields from the API response"` | `"read the form fields from the ha-mcp tool response"` |
| Lines 71–82: dashboard links | Uses `PI_IP=$(hostname -I)` | Use `homeassistant.local` per existing feedback memory (mDNS is set up by install skill) |

#### Detailed TOOLS.md changes

| Location | Current | New |
|---|---|---|
| Quick Reference table | References curl endpoints and SmartHub API | Reference ha-mcp tool names |
| Skill Auto-Generation section (lines 36–97) | Template uses `curl http://localhost:${API_PORT}/api/devices` and instructs LLM to write curl examples in new skill files | Template uses `ha_search_entities` / `ha_get_state` and instructs LLM to write ha-mcp tool call syntax in new skill files |
| Auto-generation steps | `API_PORT`-based device listing | `ha_search_entities` tool calls |

#### Detailed _errors.md changes

ha-mcp returns `ToolError` objects instead of HTTP status codes. Mapping:

| Current (HTTP) | New (ha-mcp ToolError) | Notes |
|---|---|---|
| 404 Not Found | `ToolError: entity not found` | `ha_get_state` returns error if entity_id invalid |
| 400 Bad Request | `ToolError: invalid service data` | ha-mcp validates service call parameters |
| 503 Service Unavailable | `ToolError: connection refused` / `ToolError: timeout` | ha-mcp cannot reach HA |
| 502 Bad Gateway | N/A — no proxy layer | Removed with SmartHub API |
| Entity "unavailable" state | Still applies — `ha_get_state` returns `state: "unavailable"` | Quirk unchanged: devices like Xiaomi TV show "unavailable" but still accept commands. **"Try the command anyway" guidance stays.** WebSocket verification will confirm if the command actually worked. |

**Recovery Steps section (lines 29–54) — full rewrite:**

| Current | New |
|---|---|
| "Quick restart" block: `docker compose restart` then poll `curl localhost:${API_PORT}/api/health` | Replace with: `docker compose restart homeassistant` then poll `curl -s ${HA_URL}/api/ \| grep -q "API running"`. No API health check — ha-mcp has no persistent process to poll. |
| "Reload a specific integration" block: uses `curl` to list config entries and reload | Replace with: `ha_config_entries_get` to list entries, then `ha_call_service` with `domain: homeassistant, service: reload_config_entry` or describe using ha-mcp reload tools. |
| Reference to "Step 3b for resolution" (line 26) | Remove — Step 3b is deleted. Replace with: "Check `tools/setup.md` for port conflict resolution." |

**HA Issues table (lines 19–26) — specific changes:**

| Row | Current | New |
|---|---|---|
| "All devices unavailable" | Uses `curl -s -X POST ${HA_URL}/api/config/config_entries/entry/<entry_id>/reload` | Replace with ha-mcp tool call syntax |
| "API timeout" | References `curl -s ${HA_URL}/api/` | Keep — this checks HA directly, not SmartHub API |
| "Port conflict" | References "Step 3b for resolution" | Remove row or update to reference only HA port conflicts (no API port) |

#### Detailed integrations/_guide.md changes

| Location | Current | New |
|---|---|---|
| Step 0: availability check (lines 12–22) | `curl -s http://localhost:8123/api/config/config_entries/flow_handlers` | `ha_config_entries_get` or `ha_list_services` to check domain availability |
| HACS detection (line 27) | `curl ... flow_handlers \| grep -q hacs` | `ha_hacs_search` tool — if tool not available, HACS not installed |
| HACS activation flow (lines 72–76) | `curl -s -X POST http://localhost:8123/api/config/config_entries/flow -d '{"handler": "hacs"}'` | `ha_config_entries_flow` tool |
| HA restart + wait loop (lines 62–67, 94–97) | `curl -s -X POST .../services/homeassistant/restart` + poll loop | `ha_call_service` domain=homeassistant service=restart + wait for HA API |
| Step 4: verify integration available (line 102) | `curl -s .../config/config_entries/flow_handlers \| grep` | `ha_config_entries_get` to check if domain is now present |
| Dashboard link (lines 114–116) | `PI_IP=$(hostname -I \| awk '{print $1}')` + `http://${PI_IP}:${HA_PORT}/...` | Use `homeassistant.local` per mDNS feedback memory |
| Start config flow (lines 140–145) | `curl -s -X POST .../config/config_entries/flow -d '{"handler": "<integration>"}'` | `ha_config_entries_flow` tool (start) |
| Submit step choices (lines 190–193) | `curl -s -X POST .../config/config_entries/flow/<flow_id>` | `ha_config_entries_flow` tool (submit step) |
| After completion verify (line 245) | `curl -s http://localhost:${API_PORT}/api/devices` | `ha_search_entities` to confirm new devices appeared |
| Clear stale flows (lines 258–259) | `curl -s -X DELETE .../config/config_entries/flow/<flow_id>` | `ha_config_entries_flow` tool (delete) |
| `create_entry` response handling (line 203) | "Run `/api/devices` to show what devices were found" | Use `ha_search_entities` to show new devices |

#### Detailed automations/_guide.md changes

The REST API Reference section (lines 19–75) contains 9 curl commands that must all be migrated:

| Operation | Current (curl) | New (ha-mcp) |
|---|---|---|
| Create automation (lines 27–32) | `curl -s -X POST .../api/config/automation/config/<id>` | `ha_config_set_automation` with config dict |
| Delete automation (lines 36–39) | `curl -s -X DELETE .../api/config/automation/config/<id>` | `ha_config_delete_automation` |
| Enable automation (lines 42–47) | `curl -s -X POST .../api/services/automation/turn_on` | `ha_call_service` domain=automation service=turn_on |
| Disable automation (lines 50–55) | `curl -s -X POST .../api/services/automation/turn_off` | `ha_call_service` domain=automation service=turn_off |
| Trigger automation (lines 58–63) | `curl -s -X POST .../api/services/automation/trigger` | `ha_call_service` domain=automation service=trigger |
| Reload automations (lines 66–69) | `curl -s -X POST .../api/services/automation/reload` | `ha_call_service` domain=automation service=reload |
| List automations (lines 72–74) | `curl -s .../api/states \| jq` | `ha_search_entities` filtered to automation domain |
| Auth header setup (lines 22–23) | `HA_TOKEN=$(grep HA_TOKEN .env \| cut -d= -f2)` | Remove — ha-mcp handles auth internally |
| Workflow step 7 (line 13) | "Create via API — POST the JSON to HA" | "Create via ha-mcp — use `ha_config_set_automation` tool" |

The rest of the file (Required Details Checklist, Per-Domain Trigger Reference, Recording Created Automations, Important Notes) is HA-level documentation — no API calls, no changes needed.

#### Detailed _common.md rewrite and _ha-mcp.md content

**`tools/_common.md`** (119 lines) is entirely curl-based and must be rewritten. New structure:

```markdown
# Common — ha-mcp Tool Reference

## How Device Control Works

All HA interaction goes through ha-mcp tools (MCP protocol, stdio).
No curl. No API routing. No ports to configure.

ha-mcp handles authentication internally via HOMEASSISTANT_TOKEN env var.

## Commonly Used Tools

### Search entities
Tool: ha_search_entities
  query: "<search term>"

### Get entity state
Tool: ha_get_state
  entity_id: "<entity_id>"

### Call a service (device control)
Tool: ha_call_service
  domain: "<domain>"
  service: "<service>"
  entity_id: "<entity_id>"
  data: { ... }

### List areas
Tool: ha_get_areas

### Config entries
Tool: ha_config_entries_get

## Network Info
- Home Assistant: http://homeassistant.local:<HA_PORT>
- ha-mcp: stdio process (no port, no URL)
- mDNS: homeassistant.local resolves to the Pi's IP on the LAN
```

Sections removed from `_common.md`:
- "API Routing Rule" (line 11–16) — no routing, all through ha-mcp
- "SmartHub API" section (lines 18–52) — replaced by ha-mcp tools above
- "Home Assistant Direct API" section (lines 56–109) — replaced by ha-mcp tools
- "Network Info" SmartHub API line (line 116) — removed

**`tools/_ha-mcp.md`** (new file) content structure:

```markdown
# ha-mcp — Tool Reference

Quick reference for the most-used ha-mcp tools. Full list: use `ha_search_tools`.

## Device Control
| Task | Tool | Key params |
|---|---|---|
| Turn on/off | ha_call_service | domain, service, entity_id |
| Check state | ha_get_state | entity_id |
| Find entities | ha_search_entities | query |
| List areas | ha_get_areas | — |

## Automation Management
| Task | Tool | Key params |
|---|---|---|
| Create | ha_config_set_automation | config dict |
| Delete | ha_config_delete_automation | automation_id |
| Get config | ha_config_get_automation | automation_id |
| Debug traces | ha_get_automation_traces | automation_id |

## Integration Management
| Task | Tool | Key params |
|---|---|---|
| List config entries | ha_config_entries_get | — |
| Start config flow | ha_config_entries_flow | handler |
| HACS search | ha_hacs_search | query |
| HACS download | ha_hacs_download | repository |

## Helpers
| Task | Tool | Key params |
|---|---|---|
| Create helper | ha_create_helper | type, name |
| List services | ha_list_services | domain (optional) |

## Tool Search
When you don't know the right tool, use:
Tool: ha_search_tools
  query: "<what you want to do>"
```

#### Detailed install.sh changes

Existing blocks to modify:

| Lines | Current | Action |
|---|---|---|
| 1–10 | Shebang, intro text | Keep, update intro text (remove "SmartHub API" mention) |
| 11–45 | Clone repo, detect OpenClaw workspace | Keep as-is |
| 46–80 | Patch `openclaw.json` bootstrap-extra-files | Keep as-is |
| 81–100 | Create .env from .env.example | Keep, but remove `API_PORT` prompt/default |
| 101–136 | HA port conflict resolution | Keep as-is |
| 137–148 | **API port conflict resolution** | **DELETE** — no API port needed |
| 149–152 | Blank/separator | Keep |
| 153–157 | **`npm install` in api/** | **REPLACE** with: install uv (`curl -LsSf https://astral.sh/uv/install.sh \| sh`), then `uvx ha-mcp@7.2.0 --help >/dev/null 2>&1` to verify install |
| 158–164 | MCP config decision | **ADD**: `if openclaw mcp list 2>/dev/null; then` patch `openclaw.json` mcp.servers; `else` write `.claude/settings.json` mcpServers; `fi`. The check passes if `openclaw mcp list` exits 0 (command exists AND MCP subsystem is initialized). |
| 165–170 | `AI_INSTRUCTION` output referencing Steps 3, 3b | **UPDATE**: remove Step 3b (API port) reference, update to reflect ha-mcp setup flow |
| 171–173 | Done message | Keep, update wording |

#### Detailed setup.md changes

| Step | Current | Action |
|---|---|---|
| Step 1–2 | Docker setup, HA config | Keep as-is |
| Step 3 | HA port assignment | Keep as-is |
| Step 3b (lines 79–119) | **API port conflict resolution** | **DELETE** entire step — no API port needed |
| Step 4–7 | Token creation, .env setup | Keep, remove `API_PORT` references |
| Step 8 (lines 272–288) | **Restart the API: `docker compose restart api`** | **DELETE** or replace with: "Verify ha-mcp can reach HA" (no restart needed — ha-mcp is spawned on demand, not a persistent service) |
| Step 9 (lines 290–303) | **Verify: `curl localhost:3001/api/devices`** | **REPLACE** with ha-mcp smoke test (see smoke-test section). Success output: "Connected to Home Assistant at <URL>. Found N entities." |
| Step 10 (lines 305–317) | "SmartHub is ready!" + next steps | **UPDATE** wording: "ha-mcp is ready!" — remove SmartHub branding from setup completion message |

### Files added

| File | Purpose |
|---|---|
| `tools/_ha-mcp.md` | Skill file documenting commonly used ha-mcp tools and patterns for the LLM. |

**Note:** `scripts/approval_gate.py` is NOT created during this migration. It depends on the Layer 2 research spike (see Approval Gating section). It will be added as a separate deliverable once the OpenClaw hook interface is confirmed.

### Skill file syntax migration

**Before (curl to SmartHub API):**
```markdown
## Turn off a light
POST http://localhost:3001/api/services/light/turn_off
Body: { "entity_id": "light.living_room" }
```

**After (ha-mcp tool call):**
```markdown
## Turn off a light
Tool: ha_call_service
  domain: "light"
  service: "turn_off"
  entity_id: "light.living_room"
```

Device-specific quirks stay unchanged — they describe HA-level behavior, not API-level details.

### ha-mcp skills vs our skill files

ha-mcp bundles general HA best-practice skills (automation patterns, helper selection, etc.). Our `tools/` files have device-specific knowledge (Xiaomi TV quirks, printer setup, AC service data format).

They complement each other:
- **ha-mcp skills**: how to use HA properly (general)
- **Our skill files**: what we know about specific devices (specific)

Keep both. No conflict. No deduplication needed.

---

## Setup & Install Flow

### Updated install.sh

1. **Check Python 3.13+** — ha-mcp requires `>=3.13,<3.14` (per its `pyproject.toml`). Raspberry Pi OS Bookworm ships 3.11. Use `uvx` which manages its own Python — install uv first: `curl -LsSf https://astral.sh/uv/install.sh | sh`. This avoids needing to install Python 3.13 system-wide.
2. **Install ha-mcp** — `uvx ha-mcp@7.2.0` (pinned version). uvx handles the Python 3.13 requirement automatically via its managed toolchain.
3. Clone/update this repo into OpenClaw workspace (same as today)
4. **Patch `openclaw.json`** — add `bootstrap-extra-files` hook (same as today). MCP server config: if OpenClaw native MCP is available, add to `mcp.servers`; otherwise configure in `.claude/settings.json` for the Claude Code bridge. Decision rule: check `openclaw mcp list 2>/dev/null` — if it succeeds, use `openclaw.json`; if it fails, use `.claude/settings.json`.
5. Resolve port conflicts for HA (same, but no API port needed)
6. Start Docker — `docker compose up -d` (one container: Home Assistant)
7. Print success and continue with `tools/setup.md`

### Updated first-run check (CLAUDE.md)

```bash
# 1. Does .env exist with a token?
grep -q 'HA_TOKEN=.' .env 2>/dev/null && echo "ENV_OK" || echo "ENV_MISSING"

# 2. Is Home Assistant reachable?
HA_URL=$(grep HA_URL .env 2>/dev/null | cut -d= -f2)
curl -s --max-time 5 ${HA_URL:-http://localhost:8123}/api/ 2>/dev/null | grep -q "API running" && echo "HA_OK" || echo "HA_DOWN"

# 3. Is ha-mcp installed and can it reach HA?
HOMEASSISTANT_TOKEN=$(grep HA_TOKEN .env 2>/dev/null | cut -d= -f2) \
HOMEASSISTANT_URL=$(grep HA_URL .env 2>/dev/null | cut -d= -f2) \
uvx ha-mcp@7.2.0 --smoke-test 2>/dev/null && echo "MCP_OK" || echo "MCP_DOWN"
```

**Important:** Check 3 requires `HOMEASSISTANT_TOKEN` and `HOMEASSISTANT_URL` env vars — ha-mcp uses these to connect to HA. Without them, the smoke test fails even if ha-mcp is installed correctly.

**Verification of `--smoke-test` flag:** This flag exists in ha-mcp's `__main__.py` (confirmed in ha-mcp v7.2.0 source). It tests: (1) ha-mcp binary is installed, (2) Python 3.13 is available via uvx, (3) HA is reachable at the configured URL, (4) the token is valid.

**Fallback if `--smoke-test` does not exist in the pinned version:** Use `uvx ha-mcp@7.2.0 --help 2>/dev/null && echo "MCP_INSTALLED" || echo "MCP_MISSING"` to verify ha-mcp binary installation, then rely on check #2 (HA reachable) for connectivity. This degrades gracefully — we lose the combined check. Note: the fallback does NOT verify Python 3.13 availability (uvx may resolve the binary without the right Python). This is an acceptable residual risk since uvx manages its own Python toolchain.

### Updated setup.md verify step

```bash
HOMEASSISTANT_TOKEN=$(grep HA_TOKEN .env | cut -d= -f2) \
HOMEASSISTANT_URL=$(grep HA_URL .env | cut -d= -f2) \
uvx ha-mcp@7.2.0 --smoke-test
```

Replaces `curl localhost:3001/api/devices`. Tests end-to-end: ha-mcp installed, Python 3.13 available, HA reachable, token valid. Expected success output: "Connected to Home Assistant at <URL>." Expected failure output: error message indicating which component failed (installation, Python version, HA connectivity, or token).

---

## Interim Bridge (Claude Code)

Until OpenClaw ships native MCP support (tracked in openclaw/openclaw#4834):

**Path:** OpenClaw → ACPX plugin → Claude Code → ha-mcp (stdio) → HA

**Config:** ha-mcp is configured in `.claude/settings.json` (project-level). When OpenClaw spawns Claude Code via ACPX, Claude Code starts ha-mcp as a child process and all 87 tools are available.

**Interim approval gating limitation:** During the Claude Code bridge phase, Layer 1 (OpenClaw annotation handling) and Layer 2 (OpenClaw hooks) are not available — OpenClaw is not the MCP client, Claude Code is. Claude Code does prompt for tool approval, but the mechanism is Claude Code's own permission system, not messaging platform confirmation. **Only Layer 3 (CLAUDE.md rules) provides the "ask user via messaging platform" behavior during the interim.** This is the same level of protection as the current system — no regression, but no improvement until native MCP ships.

**Interim latency trade-off:** The interim path adds a hop (OpenClaw → Claude Code → ha-mcp) compared to the native path. Beta users already flagged latency. This may make latency slightly worse during the interim period. The tool search transform (`ENABLE_TOOL_SEARCH=true`) partially offsets this by reducing context window size. The native MCP path removes the extra hop.

**Migration to native MCP:** Move MCP config from `.claude/settings.json` to `openclaw.json` under `mcp.servers`. Remove Claude Code middleman. Everything else stays identical — skill files, CLAUDE.md, approval gating, ha-mcp setup.

**The migration is a config change, not a code change.**

```
Interim:   OpenClaw → ACPX → Claude Code → ha-mcp → HA
Native:    OpenClaw → ha-mcp → HA
```

---

## What We Gain

| Capability | Before (SmartHub API) | After (ha-mcp) |
|---|---|---|
| Tool count | ~6 endpoints | 87 structured tools |
| State verification | Assume success | WebSocket confirmation |
| HACS integration | Not supported | `ha_hacs_search`, `ha_hacs_download` |
| Dashboard editing | Not supported | Full dashboard CRUD |
| Automation debugging | Not supported | `ha_get_automation_traces` |
| Backup/restore | Not supported | `ha_backup_create`, `ha_backup_restore` |
| Helper management | Not supported | Full helper CRUD |
| Approval gating | LLM rules only | Annotations + LLM rules (2 layers at launch; hook layer contingent on research spike) |
| Maintenance burden | Custom TypeScript server | Community-maintained (2100+ stars) |
| Docker containers | 2 (HA + API) | 1 (HA only) |
| Context window cost | N/A | Tool search reduces token usage |

---

## Migration Safety

### Rollback plan

Before removing the `api/` directory, tag the current state:

```bash
git tag pre-ha-mcp-migration
```

If ha-mcp has a blocking issue post-migration, revert:

```bash
git checkout pre-ha-mcp-migration -- api/ docker-compose.yml .env.example
docker compose up -d
```

This restores the SmartHub API alongside ha-mcp. Both can coexist — they use different ports and protocols.

### Parallel run period

Before deleting `api/`, run both systems simultaneously for at least one week:
1. ha-mcp connected via MCP (new path)
2. SmartHub API still running in Docker (old path, unused but available)

**Verification checklist** — all must pass before removing `api/`:

| SmartHub API endpoint | ha-mcp equivalent | Test command |
|---|---|---|
| `GET /api/devices` | `ha_search_entities` | Search for a known entity (e.g., `media_player.edgenesis_tv`) and verify it returns |
| `GET /api/devices/:id` | `ha_get_state` | Get state of a specific entity and verify attributes match |
| `GET /api/areas` | `ha_get_areas` | List areas and verify count matches HA dashboard |
| `POST /api/services/:domain/:service` | `ha_call_service` | Turn a light/switch on and off, verify via WebSocket state change |
| `GET /api/camera/:entity_id/snapshot` | HA native `/api/camera_proxy/<entity_id>` | Verify camera snapshot is accessible (if camera entities exist) |
| Xiaomi config flow (`/api/xiaomi/*`) | `ha_config_entries_flow` tools | Not re-tested during parallel run — only needed during initial setup |
| Entity "unavailable" recovery | `ha_call_service` + WebSocket verification | Call service on an "unavailable" entity (e.g., Xiaomi TV), verify it still works |

Only after all applicable rows pass → remove `api/`.

### Version pinning

Pin ha-mcp to a specific minor version in all configs:

```
uvx ha-mcp@7.2.0
```

Update deliberately after testing, not automatically. ha-mcp is actively developed — breaking changes happen (e.g., v7.0.0 had a breaking OAuth change).

---

## 2026-04-10 Correction — ha-mcp 7.2.0 Bundled Skills Claim

**Added by:** `rdw-20260410-skill-audit` workflow
**Affects:** Primarily lines 496-504 ("ha-mcp skills vs our skill files"); secondary context at lines 58, 120-121, and 472.
**Original content preserved above** — this is an append-only correction, not an in-place edit.

The "ha-mcp skills vs our skill files" section above (lines 496-504) asserts that ha-mcp bundles general HA best-practice skills (automation patterns, helper selection, etc.). A verification pass on 2026-04-10 discovered this is **false for the PyPI wheel** that SmartHub installs via `uvx ha-mcp@7.2.0`.

**Evidence** (see `docs/rdw-state-skill-audit.json` Discovery D1 for full details):
- The wheel `RECORD` at `~/.cache/uv/archive-v0/*/lib/python3.13/site-packages/ha_mcp-7.2.0.dist-info/RECORD` contains zero `.md` files and no `resources/` directory entries.
- `ha_mcp/server.py:146` `_get_skills_dir()` returns `None` because `resources/skills-vendor/skills/` does not exist in the installed package.
- `ha_mcp/server.py:471` `_register_skills()` logs a warning and exits early when `skills_dir is None`.
- `ListMcpResourcesTool` for the `ha-mcp` server returns "No resources found" at runtime.
- The `ENABLE_SKILLS=true` and `ENABLE_SKILLS_AS_TOOLS=true` env vars in `.claude/settings.json` silently have no effect — there are no skills to load.

**Root cause:** The `resources/skills-vendor/` directory is a git submodule in the ha-mcp source repository and gets stripped from the PyPI wheel build. The code paths exist but never fire for wheel-installed users.

**Impact on the migration design:** The statement "ha-mcp bundles general HA best-practice skills" and the "Keep both. No conflict. No deduplication needed." conclusion remain **operationally correct** — we still keep both sets of files — but the *reason* cited was wrong. SmartHub's `tools/*.md` files are complementary to **raw ha-mcp tool schemas**, not to bundled ha-mcp skills, because there are no bundled ha-mcp skills. This changes how future contributors should think about deduplication: the reference point is the MCP tool schema layer, not a parallel skill layer.

**Follow-up:** Potential upstream packaging bug in ha-mcp deferred (not filed with homeassistant-ai/ha-mcp). Re-evaluate if a future ha-mcp release ships the `resources/skills-vendor/` submodule in the wheel.
