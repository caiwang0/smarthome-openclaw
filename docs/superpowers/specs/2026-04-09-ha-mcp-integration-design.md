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
- ha-mcp installed via uvx, runs as stdio MCP server (pinned to v7.2.x)
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

### Layer 2: OpenClaw hook (fallback)

If OpenClaw's MCP client does not respect annotations, use a pre-execution hook. The exact hook shape depends on OpenClaw's hook system at time of implementation — the `hooks` config section already exists in `openclaw.json`, but the MCP-specific hook interface (`mcp-tool-before`) is not yet documented. This layer is **contingent** on OpenClaw exposing a pre-execution hook for MCP tool calls.

Conceptual design:

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

`scripts/approval_gate.py` (~50 lines):
- Reads tool name and annotations from args
- If `destructiveHint: true`: sends confirmation message via OpenClaw's messaging API (exact API surface TBD — depends on OpenClaw's SDK at time of implementation)
- If approved: exits 0 (tool executes)
- If rejected: exits 1 (tool blocked)

**If OpenClaw supports neither annotations nor pre-execution hooks**, do not build a custom proxy. Escalate and rely on Layer 3 until OpenClaw adds support.

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
  src/index.ts
  src/ha-client.ts
  src/device-aggregator.ts
  src/types.ts
  src/routes/
  Dockerfile
  package.json
  bun.lock
```

### Files modified

| File | Change |
|---|---|
| `docker-compose.yml` | Remove `api` service. Only `homeassistant` remains. |
| `.env.example` | Remove `API_PORT`. Keep `HA_URL`, `HA_TOKEN`, `TZ`. |
| `CLAUDE.md` | Replace "How to Interact with HA" section. Remove SmartHub API references. Update first-run check (check ha-mcp installed instead of API reachable). |
| `TOOLS.md` | Update skill router — reference ha-mcp tools instead of curl endpoints. |
| `tools/_common.md` | Biggest rewrite. Replace API routing rule, curl patterns, auth token instructions with ha-mcp tool reference guide. |
| `tools/_errors.md` | Update error handling — ha-mcp returns structured `ToolError` objects instead of HTTP status codes. |
| `tools/_services.md` | Simplify — point to `ha_list_services` tool instead of manual service list. |
| `tools/automations/_guide.md` | Replace manual JSON POST workflow with `ha_config_set_automation` / `ha_config_get_automation` tool calls. |
| `tools/automations/_reference.md` | Keep JSON schema — LLM still needs automation structure for the config dict. |
| `tools/integrations/_guide.md` | Replace manual config flow steps with ha-mcp config entry flow tools. |
| Device skill files (`tools/xiaomi-home/*.md`, etc.) | Replace curl examples with ha-mcp tool call syntax. Device quirks unchanged. |
| `install.sh` | Remove `npm install` in api/. Install uv + ha-mcp via uvx (pinned version). Configure MCP connection: use `openclaw.json` if native MCP available, otherwise `.claude/settings.json`. |
| `tools/setup.md` | Remove API restart step. Change verify step to `ha-mcp --smoke-test`. Remove API health check. |

### Files added

| File | Purpose |
|---|---|
| `scripts/approval_gate.py` | Fallback approval hook (~50 lines). Only needed if OpenClaw doesn't respect tool annotations. |
| `tools/_ha-mcp.md` | Skill file documenting commonly used ha-mcp tools and patterns for the LLM. |

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
HA_URL=$(grep HA_URL .env | cut -d= -f2)
curl -s --max-time 5 ${HA_URL:-http://localhost:8123}/api/ | grep -q "API running" && echo "HA_OK" || echo "HA_DOWN"

# 3. Is ha-mcp installed and can it reach HA?
ha-mcp --smoke-test 2>/dev/null && echo "MCP_OK" || echo "MCP_DOWN"
```

Check 3 uses `ha-mcp --smoke-test` (a real CLI flag — see `__main__.py`) which tests both installation and HA connectivity, not just PATH presence.

### Updated setup.md verify step

```bash
ha-mcp --smoke-test
```

Replaces `curl localhost:3001/api/devices`. Tests end-to-end: ha-mcp installed, Python 3.13 available, HA reachable, token valid.

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
| Approval gating | LLM rules only | Annotations + hook + LLM rules (3 layers) |
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

Verify ha-mcp handles all operations the SmartHub API did. Only then remove `api/`.

### Version pinning

Pin ha-mcp to a specific minor version in all configs:

```
uvx ha-mcp@7.2.0
```

Update deliberately after testing, not automatically. ha-mcp is actively developed — breaking changes happen (e.g., v7.0.0 had a breaking OAuth change).
