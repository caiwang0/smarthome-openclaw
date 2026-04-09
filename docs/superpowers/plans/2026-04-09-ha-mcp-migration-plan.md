# ha-mcp Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the custom SmartHub API server with ha-mcp (stock, unmodified, v7.2.0) as the sole HA communication layer — gaining 87 structured tools, WebSocket state verification, and community maintenance.

**Architecture:** OpenClaw → ha-mcp (stdio, MCP protocol) → HA (REST + WebSocket). Interim bridge: OpenClaw → ACPX → Claude Code → ha-mcp → HA. No custom API server. No fork of ha-mcp.

**Tech Stack:** ha-mcp v7.2.0 (via uvx), Home Assistant (Docker), Claude Code MCP bridge (interim), uv package manager

**Intent Priority:** Reliability > Safety > Simplicity > Latency

**Issue Doc:** `docs/superpowers/specs/2026-04-09-ha-mcp-integration-design.md`

**Key Constraints:**
- ha-mcp is used stock. No fork.
- Layer 2 approval gating is blocked on research spike — do NOT implement `scripts/approval_gate.py`
- `api/` directory is NOT deleted until parallel run verification passes (Phase 6)
- Use `homeassistant.local` for user-facing links (mDNS feedback memory)

---

## File Map

### Create
| File | Purpose |
|---|---|
| `.claude/settings.json` | ha-mcp MCP server config (interim Claude Code bridge) |
| `tools/_ha-mcp.md` | ha-mcp tool quick reference for the LLM |

### Modify
| File | Change Scope |
|---|---|
| `docker-compose.yml` | Remove `api` service (lines 14–26) |
| `.env.example` | Remove `API_PORT` line |
| `install.sh` | Remove API port logic, replace npm with uv/ha-mcp, add MCP config |
| `tools/_common.md` | Full rewrite: curl/API routing → ha-mcp tool reference |
| `tools/_errors.md` | Full rewrite: HTTP errors → ToolError patterns |
| `tools/_services.md` | Update header line |
| `CLAUDE.md` | Update first-run check, HA interaction section, references |
| `TOOLS.md` | Update Quick Reference table, Skill Auto-Generation template |
| `tools/automations/_guide.md` | Replace REST API Reference section with ha-mcp tools |
| `tools/automations/_reference.md` | Add header note |
| `tools/integrations/_guide.md` | Replace all curl commands with ha-mcp tools |
| `tools/xiaomi-home/_integration.md` | Replace curl setup command |
| `tools/xiaomi-home/tv.md` | Replace curl commands with ha-mcp tool calls |
| `tools/xiaomi-home/ma8-ac.md` | Replace curl commands with ha-mcp tool calls |
| `tools/xiaomi-home/p1v2-cooker.md` | Replace curl commands with ha-mcp tool calls |
| `tools/setup.md` | Remove Step 3b, update Steps 8–10 |
| `README.md` | Update architecture diagram, project structure, requirements |

### Delete (Phase 6, gated on parallel run)
| File | Notes |
|---|---|
| `api/` | Entire directory — only after parallel run verification passes |

### No Change
| File | Reason |
|---|---|
| `tools/printer/office-printer.md` | CUPS-based, not HA API |
| `tools/automations/_reference.md` body | JSON schema is HA-level, unchanged (only header note added) |
| `ha-config/` | Docker volume, untouched |

---

## Phase 1: Infrastructure & Safety Net

**Goal:** Create rollback point, remove API service from Docker, set up ha-mcp MCP config. After this phase, the infrastructure is ready for ha-mcp but skill files still reference the old API.

**Parallelizable:** All 4 tasks are independent.

### Task 1.1: Create rollback tag

**Files:** None (git operation)

- [ ] **Step 1: Tag the current state**

```bash
git tag pre-ha-mcp-migration
```

- [ ] **Step 2: Verify tag**

```bash
git tag -l 'pre-ha-mcp*'
```

Expected: `pre-ha-mcp-migration`

- [ ] **Step 3: Document rollback procedure**

If ha-mcp has a blocking issue post-migration, the rollback command is:

```bash
git checkout pre-ha-mcp-migration -- api/ docker-compose.yml .env.example
docker compose up -d
```

This restores the SmartHub API alongside ha-mcp. Both can coexist — they use different ports and protocols. No need to run this now — just documenting it for reference.

---

### Task 1.2: Remove API service from docker-compose.yml

**Files:**
- Modify: `docker-compose.yml:14-26`

- [ ] **Step 1: Remove the api service block**

Remove lines 14–26 (the entire `api:` service definition). The file should contain only the `homeassistant` service:

```yaml
services:
  homeassistant:
    image: "ghcr.io/home-assistant/home-assistant:stable"
    volumes:
      - ./ha-config:/config
      - /etc/localtime:/etc/localtime:ro
      - /run/dbus:/run/dbus:ro
    restart: unless-stopped
    privileged: true
    network_mode: host
    environment:
      TZ: ${TZ:-Asia/Kuala_Lumpur}
```

- [ ] **Step 2: Verify valid YAML**

```bash
docker compose config --quiet 2>&1 && echo "VALID" || echo "INVALID"
```

Expected: `VALID`

- [ ] **Step 3: Commit**

```bash
git add docker-compose.yml
git commit -m "infra: remove SmartHub API service from docker-compose

ha-mcp replaces the API server. api/ directory kept for parallel run period."
```

---

### Task 1.3: Remove API_PORT from .env.example

**Files:**
- Modify: `.env.example:4-5`

- [ ] **Step 1: Remove the API section**

Remove lines 4-5 (`# API` comment and `API_PORT=3001`). New file:

```
# Home Assistant
HA_URL=http://localhost:8123
HA_TOKEN=your_long_lived_access_token_here

# Timezone
TZ=Asia/Kuala_Lumpur
```

- [ ] **Step 2: Verify no API_PORT reference**

```bash
grep -c 'API_PORT' .env.example
```

Expected: `0`

- [ ] **Step 3: Commit**

```bash
git add .env.example
git commit -m "infra: remove API_PORT from .env.example

ha-mcp runs as stdio process, no port needed."
```

---

### Task 1.4: Create MCP server config (interim bridge)

**Files:**
- Create: `.claude/settings.json`

- [ ] **Step 1: Create the directory and config file**

```bash
mkdir -p .claude
```

Write `.claude/settings.json`:

```json
{
  "mcpServers": {
    "ha-mcp": {
      "command": "uvx",
      "args": ["ha-mcp@7.2.0"],
      "env": {
        "HOMEASSISTANT_URL": "${HA_URL}",
        "HOMEASSISTANT_TOKEN": "${HA_TOKEN}",
        "ENABLE_SKILLS": "true",
        "ENABLE_SKILLS_AS_TOOLS": "true",
        "ENABLE_TOOL_SEARCH": "true",
        "ENABLE_WEBSOCKET": "true"
      }
    }
  }
}
```

- [ ] **Step 2: Verify valid JSON**

```bash
python3 -c "import json; json.load(open('.claude/settings.json')); print('VALID')"
```

Expected: `VALID`

- [ ] **Step 3: Commit**

```bash
git add .claude/settings.json
git commit -m "infra: add ha-mcp MCP server config for Claude Code bridge

Interim config until OpenClaw ships native MCP support.
Pin ha-mcp to v7.2.0. Enable skills, tool search, and WebSocket."
```

---

## Phase 2: Core Skill Files

**Goal:** Rewrite the foundational skill files that all other files reference. After this phase, `_common.md`, `_errors.md`, `_services.md`, `CLAUDE.md`, and `TOOLS.md` all reference ha-mcp instead of curl/SmartHub API.

**Parallelizable:** All 6 tasks are independent (they follow the same ha-mcp tool call pattern from the spec).

### Task 2.1: Rewrite tools/_common.md

**Files:**
- Modify: `tools/_common.md` (full rewrite, 119 lines → ~40 lines)

- [ ] **Step 1: Replace the entire file**

```markdown
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
```

- [ ] **Step 2: Verify no legacy references**

```bash
grep -cE 'API_PORT|SmartHub|curl|API Routing' tools/_common.md
```

Expected: `0`

- [ ] **Step 3: Commit**

```bash
git add tools/_common.md
git commit -m "docs: rewrite _common.md for ha-mcp tool reference

Replace SmartHub API curl patterns and API routing rule with ha-mcp
tool call syntax. Remove all port configuration references."
```

---

### Task 2.2: Create tools/_ha-mcp.md

**Files:**
- Create: `tools/_ha-mcp.md`

- [ ] **Step 1: Write the new file**

```markdown
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
```

- [ ] **Step 2: Commit**

```bash
git add tools/_ha-mcp.md
git commit -m "docs: add ha-mcp tool quick reference

New skill file documenting commonly used ha-mcp tools and patterns."
```

---

### Task 2.3: Rewrite tools/_errors.md

**Files:**
- Modify: `tools/_errors.md` (full rewrite, 55 lines)

- [ ] **Step 1: Replace the entire file**

```markdown
# Error Handling — Runtime Troubleshooting

## ha-mcp Tool Errors

| ToolError message | Meaning | Action |
|---|---|---|
| `entity not found` | Entity ID is wrong | Look up correct ID via `ha_search_entities`. Never guess entity IDs. |
| `invalid service data` | Bad parameters for service call | Check the service's required fields via `ha_list_services` for that domain. |
| `connection refused` | ha-mcp cannot reach HA | Check `docker ps`. If homeassistant is not running: `docker compose up -d`. |
| `timeout` | HA took too long to respond | Check `docker compose logs homeassistant --tail 20`. May be a transient error — retry once. |

## Entity States

| State | Meaning | Action |
|---|---|---|
| `unavailable` | Device offline or connection dropped | **Try the command anyway** — many devices (especially Xiaomi TV via DLNA) show unavailable but still respond. WebSocket verification will confirm if the command actually worked. If the command fails, tell the user the device may be powered off. |
| `unknown` | HA hasn't received state yet | Device may still be initializing after restart. Wait 30-60 seconds, then retry. |

## Home Assistant Issues

| Symptom | Likely Cause | Action |
|---|---|---|
| All devices unavailable | HA restarted or integration crashed | Check `docker compose logs homeassistant --tail 50`. Reload the integration via `ha_config_entries_get` to find the entry, then `ha_call_service` with `domain: homeassistant, service: reload_config_entry`. |
| HA unreachable | Network issue or HA overloaded | Verify HA is running: `curl -s ${HA_URL:-http://localhost:8123}/api/`. Check `.env` has correct `HA_URL`. |
| Token rejected (401) | Token expired or invalid | Have user create a new long-lived access token in HA UI and update `.env`. |

**Note:** The old "Port conflict" row (referencing Step 3b) is intentionally removed — there is no API port to conflict. HA port conflicts are handled by `install.sh` and `tools/setup.md` Step 3.

## Recovery Steps

**Quick restart (fixes most transient issues):**
```bash
docker compose restart homeassistant
# Wait for HA to come back
HA_URL=$(grep HA_URL .env | cut -d= -f2); HA_URL=${HA_URL:-http://localhost:8123}
for i in $(seq 1 15); do curl -s ${HA_URL}/api/ 2>/dev/null | grep -q "API running" && break; sleep 2; done
```

**Reload a specific integration:**
Use `ha_config_entries_get` to list entries and find the entry ID for the integration, then reload it via `ha_call_service` with `domain: homeassistant, service: reload_config_entry` and `data: { "entry_id": "<entry_id>" }`.

For persistent issues, check `tools/setup.md` for port conflict resolution.
```

- [ ] **Step 2: Verify no legacy references**

```bash
grep -cE 'API_PORT|localhost:3001|SmartHub|Step 3b' tools/_errors.md
```

Expected: `0`

- [ ] **Step 3: Commit**

```bash
git add tools/_errors.md
git commit -m "docs: rewrite _errors.md for ha-mcp ToolError patterns

Replace HTTP status codes with ha-mcp ToolError messages.
Update recovery steps to use ha-mcp tools instead of curl."
```

---

### Task 2.4: Update tools/_services.md

**Files:**
- Modify: `tools/_services.md:1-3`

- [ ] **Step 1: Replace the header**

Replace lines 1-3:

Old:
```markdown
# Services by Domain — Quick Reference

> Use the SmartHub API for all device control: `http://localhost:${API_PORT}/api/services/<domain>/<service>`
```

New:
```markdown
# Services by Domain — Quick Reference

> Use `ha_call_service` for all device control. For a full list of services for any domain, use `ha_list_services`.
```

The rest of the file (domain tables, brightness conversion) is HA-level documentation and stays unchanged.

- [ ] **Step 2: Verify no legacy references**

```bash
grep -cE 'API_PORT|SmartHub|localhost' tools/_services.md
```

Expected: `0`

- [ ] **Step 3: Commit**

```bash
git add tools/_services.md
git commit -m "docs: update _services.md header for ha-mcp

Point to ha_call_service and ha_list_services instead of SmartHub API URL."
```

---

### Task 2.5: Update CLAUDE.md

**Files:**
- Modify: `CLAUDE.md` (5 targeted edits)

- [ ] **Step 1: Replace first-run check #3 (line 17-18)**

Old:
```markdown
# 3. Is the SmartHub API reachable?
API_PORT=$(grep API_PORT .env | cut -d= -f2); curl -s --max-time 5 http://localhost:${API_PORT}/api/health 2>/dev/null | grep -q "ok" && echo "API_OK" || echo "API_DOWN"
```

New:
```markdown
# 3. Is ha-mcp installed and can it reach HA?
HOMEASSISTANT_TOKEN=$(grep HA_TOKEN .env 2>/dev/null | cut -d= -f2) HOMEASSISTANT_URL=$(grep HA_URL .env 2>/dev/null | cut -d= -f2) uvx ha-mcp@7.2.0 --smoke-test 2>/dev/null && echo "MCP_OK" || echo "MCP_DOWN"
```

**Smoke-test fallback:** If `--smoke-test` does not exist in the pinned version, use this degraded check instead:
```markdown
# 3. Is ha-mcp installed? (fallback — does not verify HA connectivity)
uvx ha-mcp@7.2.0 --help 2>/dev/null && echo "MCP_INSTALLED" || echo "MCP_MISSING"
```
This only verifies ha-mcp binary + Python 3.13 availability via uvx. HA connectivity is covered by check #2. Acceptable residual risk since uvx manages its own Python toolchain.

- [ ] **Step 2: Update "How to Interact" section (line 31)**

Old:
```markdown
1. Read `tools/_common.md` for API patterns, auth tokens, and the API routing rule
```

New:
```markdown
1. Read `tools/_common.md` for ha-mcp tool patterns and network info
```

- [ ] **Step 3: Update dashboard link generation (lines 72-76)**

Old:
```markdown
- Get the Pi's IP and HA port first:
  ```bash
  PI_IP=$(hostname -I | awk '{print $1}')
  HA_PORT=$(grep HA_URL .env 2>/dev/null | grep -oP ':\K[0-9]+' || echo "8123")
  ```
```

New:
```markdown
- Get the HA port first:
  ```bash
  HA_PORT=$(grep HA_URL .env 2>/dev/null | grep -oP ':\K[0-9]+' || echo "8123")
  ```
```

And update the dashboard link templates from `http://<PI_IP>:<HA_PORT>/...` to `http://homeassistant.local:<HA_PORT>/...`:

Old:
```markdown
  - Integrations → `[Open HA Integrations](http://<PI_IP>:<HA_PORT>/config/integrations/dashboard)`
  - Devices → `[Open HA Devices](http://<PI_IP>:<HA_PORT>/config/devices/dashboard)`
  - Automations → `[Open HA Automations](http://<PI_IP>:<HA_PORT>/config/automation/dashboard)`
  - Settings → `[Open HA Settings](http://<PI_IP>:<HA_PORT>/config/dashboard)`
```

New:
```markdown
  - Integrations → `[Open HA Integrations](http://homeassistant.local:<HA_PORT>/config/integrations/dashboard)`
  - Devices → `[Open HA Devices](http://homeassistant.local:<HA_PORT>/config/devices/dashboard)`
  - Automations → `[Open HA Automations](http://homeassistant.local:<HA_PORT>/config/automation/dashboard)`
  - Settings → `[Open HA Settings](http://homeassistant.local:<HA_PORT>/config/dashboard)`
```

- [ ] **Step 4: Update device lookup reference (line 89)**

Old:
```markdown
- Do NOT make up device names. Always check `/api/devices` first if unsure.
```

New:
```markdown
- Do NOT make up device names. Always check via `ha_search_entities` first if unsure.
```

- [ ] **Step 5: Update "API response" reference (line 91)**

Old:
```markdown
- **For any setup/configuration task: read the form fields from the API response and present every option to the user.** Never assume or auto-fill — each integration and each user is different.
```

New:
```markdown
- **For any setup/configuration task: read the form fields from the ha-mcp tool response and present every option to the user.** Never assume or auto-fill — each integration and each user is different.
```

- [ ] **Step 6: Verify no legacy references**

```bash
grep -cE 'API_PORT|/api/devices|API response|API routing rule|PI_IP' CLAUDE.md
```

Expected: `0`

- [ ] **Step 7: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md for ha-mcp migration

Replace first-run API health check with ha-mcp smoke test.
Update HA interaction references to ha-mcp tools.
Use homeassistant.local for dashboard links instead of PI_IP."
```

---

### Task 2.6: Update TOOLS.md

**Files:**
- Modify: `TOOLS.md` (3 targeted edits)

- [ ] **Step 1: Update Quick Reference table (line 9)**

Old:
```markdown
| [tools/_common.md](tools/_common.md) | SmartHub API, HA Direct API, auth tokens, network info, API routing rule |
```

New:
```markdown
| [tools/_common.md](tools/_common.md) | ha-mcp tool patterns, network info |
```

Add new row after `_services.md`:
```markdown
| [tools/_ha-mcp.md](tools/_ha-mcp.md) | ha-mcp tool quick reference — device control, automations, integrations, helpers |
```

- [ ] **Step 2: Update "For general API patterns" text (line 23)**

Old:
```markdown
**For general API patterns** (listing devices, calling services, managing areas), read `tools/_common.md`.
```

New:
```markdown
**For ha-mcp tool patterns** (listing devices, calling services, managing areas), read `tools/_common.md`.
```

- [ ] **Step 3: Update Skill Auto-Generation template (lines 40-97)**

Replace the device discovery command (line 41):

Old:
```markdown
1. Query `API_PORT=$(grep API_PORT .env | cut -d= -f2); curl -s http://localhost:${API_PORT}/api/devices` to discover new devices
```

New:
```markdown
1. Use `ha_search_entities` to discover new devices from the integration
```

Replace the template's "Commands" header and example (lines 80-87):

Old:
```markdown
- **Primary Entity:** Look up via `/api/devices` — pattern: `<domain>.xiaomi_*_<model_slug>`

## Commands

> Read the API port first: `API_PORT=$(grep API_PORT .env | cut -d= -f2)`

<curl examples using http://localhost:${API_PORT}/api/services/... with placeholder entity IDs>
```

New:
```markdown
- **Primary Entity:** Look up via `ha_search_entities` — pattern: `<domain>.xiaomi_*_<model_slug>`

## Commands

<ha-mcp tool call examples using ha_call_service with placeholder entity IDs>
```

- [ ] **Step 4: Verify no legacy references**

```bash
grep -cE 'API_PORT|SmartHub API|curl.*localhost' TOOLS.md
```

Expected: `0`

- [ ] **Step 5: Commit**

```bash
git add TOOLS.md
git commit -m "docs: update TOOLS.md for ha-mcp migration

Update Quick Reference table, add _ha-mcp.md entry.
Replace curl-based device discovery with ha_search_entities.
Update skill file template to use ha-mcp tool call syntax."
```

---

## Phase 3: Domain Skill Files

**Goal:** Migrate all domain-specific skill files (automations, integrations, device files) from curl/REST to ha-mcp tool call syntax. Device quirks are HA-level and stay unchanged.

**Parallelizable:** All 7 tasks are independent.

### Task 3.1: Rewrite automations/_guide.md REST API section

**Files:**
- Modify: `tools/automations/_guide.md:7,17-76`

- [ ] **Step 1: Update workflow step 7 (line 7/14)**

Old:
```markdown
7. **Create via API** — POST the JSON to HA
```

New:
```markdown
7. **Create via ha-mcp** — use `ha_config_set_automation` tool
```

- [ ] **Step 2: Replace the entire REST API Reference section (lines 17-76)**

Old content: 9 curl commands for authentication, create, delete, enable, disable, trigger, reload, and list automations.

Replace with:

```markdown
---

## ha-mcp Tool Reference

### Create an automation
```
Tool: ha_config_set_automation
  config: <JSON payload>
```
The `id` field in the config dict must be a unique descriptive slug (e.g., `lights_off_midnight`, `ac_on_when_hot`).

### Delete an automation
```
Tool: ha_config_delete_automation
  automation_id: "<automation_id>"
```

### Enable an automation
```
Tool: ha_call_service
  domain: "automation"
  service: "turn_on"
  entity_id: "automation.<automation_id>"
```

### Disable an automation
```
Tool: ha_call_service
  domain: "automation"
  service: "turn_off"
  entity_id: "automation.<automation_id>"
```

### Manually trigger an automation
```
Tool: ha_call_service
  domain: "automation"
  service: "trigger"
  entity_id: "automation.<automation_id>"
```

### Reload all automations (after manual YAML edits)
```
Tool: ha_call_service
  domain: "automation"
  service: "reload"
```

### List all automations
```
Tool: ha_search_entities
  query: "automation"
```

### Debug an automation
```
Tool: ha_get_automation_traces
  automation_id: "<automation_id>"
```
```

- [ ] **Step 3: Verify no legacy references**

```bash
grep -cE 'curl|HA_TOKEN.*grep|Bearer|localhost:8123' tools/automations/_guide.md
```

Expected: `0`

- [ ] **Step 4: Commit**

```bash
git add tools/automations/_guide.md
git commit -m "docs: migrate automations/_guide.md to ha-mcp tools

Replace 9 curl commands with ha-mcp tool call syntax.
Add ha_get_automation_traces for debugging."
```

---

### Task 3.2: Add header note to automations/_reference.md

**Files:**
- Modify: `tools/automations/_reference.md:1-5`

- [ ] **Step 1: Add ha-mcp note after the existing header**

After line 4 (`> For the creation workflow...`), add:

```markdown
>
> **To create/update automations, use the `ha_config_set_automation` tool with config dicts using the schema below.**
```

The rest of the file (JSON schema, trigger types, condition types, action types, templates) is HA-level documentation and stays unchanged.

- [ ] **Step 2: Commit**

```bash
git add tools/automations/_reference.md
git commit -m "docs: add ha-mcp tool note to automations/_reference.md"
```

---

### Task 3.3: Rewrite integrations/_guide.md

**Files:**
- Modify: `tools/integrations/_guide.md` (12 targeted edits)

This file has many curl commands to replace. Each edit below is one curl → ha-mcp migration.

- [ ] **Step 1: Replace Step 0 availability check (lines 10-22)**

Old:
```markdown
```bash
HA_TOKEN=$(grep HA_TOKEN .env | cut -d= -f2)

# Check if integration domain is available
curl -s http://localhost:8123/api/config/config_entries/flow_handlers \
  -H "Authorization: Bearer $HA_TOKEN" | python3 -c "
...
"
```
```

New:
```markdown
Use `ha_config_entries_get` to check if the integration domain is already installed:

```
Tool: ha_config_entries_get
```

Check if the target domain appears in the results. If not, the integration likely needs HACS.
```

- [ ] **Step 2: Replace HACS detection (line 27)**

Old:
```markdown
2. Check if HACS is installed: `curl -s http://localhost:8123/api/config/config_entries/flow_handlers -H "Authorization: Bearer $HA_TOKEN" | grep -q hacs && echo "HACS_OK" || echo "HACS_MISSING"`
```

New:
```markdown
2. Check if HACS is installed: use `ha_hacs_search` — if the tool is not available, HACS is not installed.
```

- [ ] **Step 3: Replace HACS activation flow (lines 72-76)**

Old:
```markdown
```bash
# Start HACS config flow
curl -s -X POST http://localhost:8123/api/config/config_entries/flow \
  -H "Authorization: Bearer $HA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"handler": "hacs"}'
```
```

New:
```markdown
Start the HACS config flow:
```
Tool: ha_config_entries_flow
  handler: "hacs"
```
```

- [ ] **Step 4: Replace HA restart + wait loop (lines 62-67, 94-97)**

Old (two instances):
```markdown
```bash
curl -s -X POST http://localhost:8123/api/services/homeassistant/restart \
  -H "Authorization: Bearer $HA_TOKEN"
...
for i in $(seq 1 30); do curl -s ${HA_URL}/api/ 2>/dev/null && break; sleep 2; done
```
```

New (both instances):
```markdown
Restart HA:
```
Tool: ha_call_service
  domain: "homeassistant"
  service: "restart"
```
Then wait for HA API to come back: `for i in $(seq 1 30); do curl -s ${HA_URL}/api/ 2>/dev/null && break; sleep 2; done`
```

Note: The HA API poll is a direct HA health check (not SmartHub API), so it stays as curl.

- [ ] **Step 5: Replace Step 4 verify (line 102)**

Old:
```markdown
```bash
curl -s http://localhost:8123/api/config/config_entries/flow_handlers \
  -H "Authorization: Bearer $HA_TOKEN" | grep -q '<integration_domain>' && echo "READY" || echo "STILL_MISSING"
```
```

New:
```markdown
Verify the integration is now available:
```
Tool: ha_config_entries_get
```
Check that the target domain appears in the results.
```

- [ ] **Step 6: Update dashboard link (lines 114-117)**

Old:
```markdown
```bash
PI_IP=$(hostname -I | awk '{print $1}')
HA_PORT=$(grep HA_URL .env 2>/dev/null | grep -oP ':\K[0-9]+' || echo "8123")
echo "http://${PI_IP}:${HA_PORT}/config/integrations/dashboard"
```
```

New:
```markdown
```bash
HA_PORT=$(grep HA_URL .env 2>/dev/null | grep -oP ':\K[0-9]+' || echo "8123")
echo "http://homeassistant.local:${HA_PORT}/config/integrations/dashboard"
```
```

Update link templates from `http://<PI_IP>:<HA_PORT>/...` to `http://homeassistant.local:<HA_PORT>/...`.

- [ ] **Step 7: Replace config flow start (lines 140-145)**

Old:
```markdown
```bash
curl -s -X POST http://localhost:8123/api/config/config_entries/flow \
  -H "Authorization: Bearer $HA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"handler": "<integration_name>"}'
```
```

New:
```markdown
```
Tool: ha_config_entries_flow
  handler: "<integration_name>"
```
```

- [ ] **Step 8: Replace submit step (lines 190-193)**

Old:
```markdown
```bash
curl -s -X POST http://localhost:8123/api/config/config_entries/flow/<flow_id> \
  -H "Authorization: Bearer $HA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"field_name": "user_choice", ...}'
```
```

New:
```markdown
```
Tool: ha_config_entries_flow
  flow_id: "<flow_id>"
  data: {"field_name": "user_choice", ...}
```
```

- [ ] **Step 9: Replace completion verify (line 245)**

Old:
```markdown
```bash
API_PORT=$(grep API_PORT .env | cut -d= -f2); curl -s http://localhost:${API_PORT}/api/devices
```
```

New:
```markdown
Use `ha_search_entities` to discover new devices from the integration.
```

- [ ] **Step 10: Replace `create_entry` handler (line 203)**

Old:
```markdown
| `create_entry` | Setup complete | Confirm success. Run `/api/devices` to show what devices were found. |
```

New:
```markdown
| `create_entry` | Setup complete | Confirm success. Use `ha_search_entities` to show what devices were found. |
```

- [ ] **Step 11: Replace stale flow deletion (lines 258-259)**

Old:
```markdown
```bash
curl -s -X DELETE http://localhost:8123/api/config/config_entries/flow/<flow_id> \
  -H "Authorization: Bearer $HA_TOKEN"
```
```

New:
```markdown
```
Tool: ha_config_entries_flow
  flow_id: "<flow_id>"
  action: "delete"
```
```

- [ ] **Step 12: Verify no legacy references**

```bash
grep -cE 'API_PORT|localhost:\$\{API_PORT\}|localhost:3001|/api/devices' tools/integrations/_guide.md
```

Expected: `0`

- [ ] **Step 13: Commit**

```bash
git add tools/integrations/_guide.md
git commit -m "docs: migrate integrations/_guide.md to ha-mcp tools

Replace all curl commands with ha-mcp tool calls.
Use homeassistant.local for dashboard links.
Keep HA restart poll as direct curl (HA health check, not SmartHub API)."
```

---

### Task 3.4: Update xiaomi-home/_integration.md

**Files:**
- Modify: `tools/xiaomi-home/_integration.md`

- [ ] **Step 1: Replace config flow curl command (lines 17-21)**

Old:
```markdown
**Start the flow:**
```bash
curl -s -X POST http://localhost:8123/api/config/config_entries/flow \
  -H "Authorization: Bearer $HA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"handler": "xiaomi_home"}'
```
```

New:
```markdown
**Start the flow:**
```
Tool: ha_config_entries_flow
  handler: "xiaomi_home"
```
```

- [ ] **Step 2: Update entity lookup reference (line 47)**

Old:
```markdown
- Entity IDs are very long (e.g., `media_player.xiaomi_cn_mitv_3b1ed2f92de5175e4cdf6f66d685ec5c_...`). Always look up the actual entity ID from `/api/devices` rather than guessing.
```

New:
```markdown
- Entity IDs are very long (e.g., `media_player.xiaomi_cn_mitv_3b1ed2f92de5175e4cdf6f66d685ec5c_...`). Always look up the actual entity ID via `ha_search_entities` rather than guessing.
```

- [ ] **Step 3: Commit**

```bash
git add tools/xiaomi-home/_integration.md
git commit -m "docs: migrate xiaomi-home/_integration.md to ha-mcp tools"
```

---

### Task 3.5: Rewrite xiaomi-home/tv.md commands

**Files:**
- Modify: `tools/xiaomi-home/tv.md`

- [ ] **Step 1: Update entity lookup reference (line 10)**

Old:
```markdown
- **Primary Entity:** Look up via `/api/devices` — entity IDs are long and auto-generated.
```

New:
```markdown
- **Primary Entity:** Look up via `ha_search_entities` — entity IDs are long and auto-generated.
```

- [ ] **Step 2: Replace all curl command blocks (lines 14-56)**

Replace the entire Commands section with:

```markdown
## Commands

### Power
```
Tool: ha_call_service
  domain: "media_player"
  service: "turn_off"
  entity_id: "<entity_id>"
```

### Volume
```
# Volume up
Tool: ha_call_service
  domain: "media_player"
  service: "volume_up"
  entity_id: "<entity_id>"

# Volume down
Tool: ha_call_service
  domain: "media_player"
  service: "volume_down"
  entity_id: "<entity_id>"

# Set volume (0.0 to 1.0)
Tool: ha_call_service
  domain: "media_player"
  service: "volume_set"
  entity_id: "<entity_id>"
  data: {"volume_level": 0.5}

# Mute/unmute
Tool: ha_call_service
  domain: "media_player"
  service: "volume_mute"
  entity_id: "<entity_id>"
  data: {"is_volume_muted": true}
```

### Playback
```
# Play
Tool: ha_call_service
  domain: "media_player"
  service: "media_play"
  entity_id: "<entity_id>"

# Pause
Tool: ha_call_service
  domain: "media_player"
  service: "media_pause"
  entity_id: "<entity_id>"
```
```

Quirks section stays unchanged.

- [ ] **Step 3: Update quirk about entity ID (line 62)**

Old:
```markdown
- **Entity ID is very long** — Never guess the entity ID. Always look it up from `/api/devices`.
```

New:
```markdown
- **Entity ID is very long** — Never guess the entity ID. Always look it up via `ha_search_entities`.
```

- [ ] **Step 4: Verify no legacy references**

```bash
grep -cE 'curl|API_PORT|/api/devices' tools/xiaomi-home/tv.md
```

Expected: `0`

- [ ] **Step 5: Commit**

```bash
git add tools/xiaomi-home/tv.md
git commit -m "docs: migrate xiaomi-home/tv.md to ha-mcp tool calls"
```

---

### Task 3.6: Rewrite xiaomi-home/ma8-ac.md commands

**Files:**
- Modify: `tools/xiaomi-home/ma8-ac.md`

- [ ] **Step 1: Update entity lookup reference (line 9)**

Old:
```markdown
- **Primary Entity:** Look up via `/api/devices` — pattern: `climate.xiaomi_*_ma8`
```

New:
```markdown
- **Primary Entity:** Look up via `ha_search_entities` — pattern: `climate.xiaomi_*_ma8`
```

- [ ] **Step 2: Replace all curl command blocks (lines 12-90)**

Replace the entire Commands section with:

```markdown
## Commands

### Power
```
# Turn on
Tool: ha_call_service
  domain: "climate"
  service: "turn_on"
  entity_id: "<entity_id>"

# Turn off
Tool: ha_call_service
  domain: "climate"
  service: "turn_off"
  entity_id: "<entity_id>"
```

### Set temperature and mode
```
Tool: ha_call_service
  domain: "climate"
  service: "set_temperature"
  entity_id: "<entity_id>"
  data: {"temperature": 24, "hvac_mode": "cool"}
```

### Set HVAC mode
```
# Modes: off, cool, heat, heat_cool, auto, dry, fan_only
Tool: ha_call_service
  domain: "climate"
  service: "set_hvac_mode"
  entity_id: "<entity_id>"
  data: {"hvac_mode": "cool"}
```

### Fan mode
```
Tool: ha_call_service
  domain: "select"
  service: "select_option"
  entity_id: "<fan_mode_select_entity>"
  data: {"option": "<mode_value>"}
```
Look up available options from the entity's attributes via `ha_get_state`.

### Horizontal swing
```
# Toggle horizontal swing on/off
Tool: ha_call_service
  domain: "switch"
  service: "turn_on"
  entity_id: "<horizontal_swing_entity>"
```

### Child lock (physical controls lock)
```
# Lock
Tool: ha_call_service
  domain: "switch"
  service: "turn_on"
  entity_id: "<physical_controls_locked_entity>"

# Unlock
Tool: ha_call_service
  domain: "switch"
  service: "turn_off"
  entity_id: "<physical_controls_locked_entity>"
```

### Delay timer
```
# Enable delay
Tool: ha_call_service
  domain: "switch"
  service: "turn_on"
  entity_id: "<delay_switch_entity>"

# Set delay time (minutes)
Tool: ha_call_service
  domain: "number"
  service: "set_value"
  entity_id: "<delay_time_entity>"
  data: {"value": 30}
```

### Indicator light
```
Tool: ha_call_service
  domain: "light"
  service: "turn_off"
  entity_id: "<indicator_light_entity>"
```
```

Key entities table stays unchanged. Quirks section stays unchanged.

- [ ] **Step 3: Remove the "Read the API port first" line (line 13)**

Old:
```markdown
> Read the API port first: `API_PORT=$(grep API_PORT .env | cut -d= -f2)`
```

Remove this line entirely.

- [ ] **Step 4: Update fan mode lookup reference (line 49)**

Old:
```markdown
Look up available options from the entity's attributes via `/api/devices`.
```

New:
```markdown
Look up available options from the entity's attributes via `ha_get_state`.
```

- [ ] **Step 5: Verify no legacy references**

```bash
grep -cE 'curl|API_PORT|/api/devices' tools/xiaomi-home/ma8-ac.md
```

Expected: `0`

- [ ] **Step 6: Commit**

```bash
git add tools/xiaomi-home/ma8-ac.md
git commit -m "docs: migrate xiaomi-home/ma8-ac.md to ha-mcp tool calls"
```

---

### Task 3.7: Rewrite xiaomi-home/p1v2-cooker.md commands

**Files:**
- Modify: `tools/xiaomi-home/p1v2-cooker.md`

- [ ] **Step 1: Update entity lookup reference (line 9)**

Old:
```markdown
- **Primary Entity:** Look up via `/api/devices` — pattern: `sensor.xiaomi_*_p1v2_status_*`
```

New:
```markdown
- **Primary Entity:** Look up via `ha_search_entities` — pattern: `sensor.xiaomi_*_p1v2_status_*`
```

- [ ] **Step 2: Replace all curl command blocks (lines 12-63)**

Replace the entire Commands section with:

```markdown
## Commands

### Cancel cooking
```
Tool: ha_call_service
  domain: "button"
  service: "press"
  entity_id: "<cancel_cooking_button_entity>"
```

### Set cooking mode
```
Tool: ha_call_service
  domain: "select"
  service: "select_option"
  entity_id: "<mode_select_entity>"
  data: {"option": "<mode_value>"}
```
Look up available cooking modes from the entity's attributes via `ha_get_state`.

### Set cook time
```
Tool: ha_call_service
  domain: "number"
  service: "set_value"
  entity_id: "<cook_time_entity>"
  data: {"value": 30}
```

### Set keep warm temperature
```
Tool: ha_call_service
  domain: "number"
  service: "set_value"
  entity_id: "<keep_warm_temp_entity>"
  data: {"value": 65}
```

### Set keep warm duration
```
Tool: ha_call_service
  domain: "number"
  service: "set_value"
  entity_id: "<keep_warm_time_entity>"
  data: {"value": 60}
```

### Toggle auto keep warm
```
Tool: ha_call_service
  domain: "switch"
  service: "turn_on"
  entity_id: "<auto_keep_warm_entity>"
```

### Toggle alarm/beep
```
Tool: ha_call_service
  domain: "switch"
  service: "turn_off"
  entity_id: "<alarm_entity>"
```
```

Key entities table stays unchanged. Quirks section stays unchanged.

- [ ] **Step 3: Remove the "Read the API port first" line (line 13)**

Old:
```markdown
> Read the API port first: `API_PORT=$(grep API_PORT .env | cut -d= -f2)`
```

Remove this line entirely.

- [ ] **Step 4: Update cooking mode lookup reference (line 28)**

Old:
```markdown
Look up available cooking modes from the entity's attributes via `/api/devices`.
```

New:
```markdown
Look up available cooking modes from the entity's attributes via `ha_get_state`.
```

- [ ] **Step 5: Verify no legacy references**

```bash
grep -cE 'curl|API_PORT|/api/devices' tools/xiaomi-home/p1v2-cooker.md
```

Expected: `0`

- [ ] **Step 6: Commit**

```bash
git add tools/xiaomi-home/p1v2-cooker.md
git commit -m "docs: migrate xiaomi-home/p1v2-cooker.md to ha-mcp tool calls"
```

---

## Phase 4: User-Facing Docs & Setup Flow

**Goal:** Update install script, setup guide, and README to reflect the ha-mcp architecture. After this phase, a fresh install would set up ha-mcp instead of the SmartHub API.

**Parallelizable:** All 3 tasks are independent.

### Task 4.1: Update install.sh

**Files:**
- Modify: `install.sh` (7 targeted edits)

- [ ] **Step 1: Update intro text (lines 3-5)**

Old:
```bash
# SmartHub for OpenClaw — One-command installer
```

New:
```bash
# SmartHub + ha-mcp for OpenClaw — One-command installer
```

Remove any other "SmartHub API" mentions in the intro/comment block (lines 1-10). Keep "SmartHub" branding, just remove "SmartHub API" specifically.

- [ ] **Step 2: Remove API_PORT from .env creation block (lines 96-99)**

The `.env` creation block copies from `.env.example`. Since `.env.example` no longer has `API_PORT` (Task 1.3), the `cp` command is fine. But if there is any explicit `API_PORT` prompt, default setting, or `sed` command in lines 81-100 that sets `API_PORT`, remove it. Verify:

```bash
grep -n 'API_PORT' install.sh
```

Remove every match that is not already deleted in other steps (i.e., lines outside 137-148).

- [ ] **Step 3: Remove API port conflict block (lines 137-148)**

Delete the entire block:
```bash
# Check API port conflict
API_PORT=$(grep API_PORT .env | cut -d= -f2)
API_PORT=${API_PORT:-3001}
if ss -tlnp 2>/dev/null | grep -q ":${API_PORT} "; then
  for port in $(seq $((API_PORT + 1)) $((API_PORT + 10))); do
    if ! ss -tlnp 2>/dev/null | grep -q ":${port} "; then
      sed -i "s|API_PORT=.*|API_PORT=${port}|" .env
      echo "API port conflict: reassigned to ${port}."
      break
    fi
  done
fi
```

- [ ] **Step 4: Replace npm install block (lines 152-156)**

Old:
```bash
# --- Install npm dependencies for the SmartHub API ---
if [ -f "$TARGET/api/package.json" ]; then
  echo "Installing API dependencies..."
  cd "$TARGET/api" && npm install --silent 2>/dev/null || true
fi
```

New:
```bash
# --- Install uv and verify ha-mcp ---
# ha-mcp requires Python >=3.13,<3.14. Raspberry Pi OS Bookworm ships 3.11.
# uvx manages its own Python toolchain — no system-wide Python 3.13 install needed.
echo "Installing uv package manager..."
curl -LsSf https://astral.sh/uv/install.sh | sh 2>/dev/null
export PATH="$HOME/.local/bin:$PATH"

echo "Verifying ha-mcp installation..."
uvx ha-mcp@7.2.0 --help >/dev/null 2>&1 && echo "ha-mcp OK" || echo "WARNING: ha-mcp verification failed"
```

- [ ] **Step 5: Add MCP config block (after the uv install block)**

Insert after the ha-mcp verification:

```bash
# --- Configure MCP server ---
cd "$TARGET"
if openclaw mcp list 2>/dev/null; then
  echo "Configuring ha-mcp in openclaw.json (native MCP)..."
  python3 -c "
import json

config_path = '$CONFIG_FILE'
with open(config_path, 'r') as f:
    config = json.load(f)

mcp = config.setdefault('mcp', {})
servers = mcp.setdefault('servers', {})
servers['ha-mcp'] = {
    'command': 'uvx',
    'args': ['ha-mcp@7.2.0'],
    'env': {
        'HOMEASSISTANT_URL': 'http://localhost:8123',
        'HOMEASSISTANT_TOKEN': '\${HA_TOKEN}',
        'ENABLE_SKILLS': 'true',
        'ENABLE_SKILLS_AS_TOOLS': 'true',
        'ENABLE_TOOL_SEARCH': 'true',
        'ENABLE_WEBSOCKET': 'true'
    }
}

with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)
print('  Configured ha-mcp in openclaw.json')
"
else
  echo "Configuring ha-mcp in .claude/settings.json (Claude Code bridge)..."
  mkdir -p "$TARGET/.claude"
  cat > "$TARGET/.claude/settings.json" << 'MCPEOF'
{
  "mcpServers": {
    "ha-mcp": {
      "command": "uvx",
      "args": ["ha-mcp@7.2.0"],
      "env": {
        "HOMEASSISTANT_URL": "${HA_URL}",
        "HOMEASSISTANT_TOKEN": "${HA_TOKEN}",
        "ENABLE_SKILLS": "true",
        "ENABLE_SKILLS_AS_TOOLS": "true",
        "ENABLE_TOOL_SEARCH": "true",
        "ENABLE_WEBSOCKET": "true"
      }
    }
  }
}
MCPEOF
fi
```

- [ ] **Step 6: Update the AI_INSTRUCTION and done message (lines 163-173)**

This covers both the AI_INSTRUCTION output block AND the done message (they are adjacent lines). Replace the entire block from the first `echo ""` through the last `echo ""`:

Old:
```bash
echo ""
echo "============================================"
echo "  SmartHub installed!"
echo "============================================"
echo ""
echo "AI_INSTRUCTION: Installation complete. DO NOT ask the user anything."
echo "Run: cd ${TARGET}"
echo "Then immediately read ${TARGET}/tools/setup.md and begin executing"
echo "the setup steps from that directory. Start from Step 2."
echo "Port conflicts and .env are already resolved — skip Step 3 and Step 3b."
echo ""
```

New:
```bash
echo ""
echo "============================================"
echo "  SmartHub + ha-mcp installed!"
echo "============================================"
echo ""
echo "AI_INSTRUCTION: Installation complete. DO NOT ask the user anything."
echo "Run: cd ${TARGET}"
echo "Then immediately read ${TARGET}/tools/setup.md and begin executing"
echo "the setup steps from that directory. Start from Step 2."
echo "Port conflicts and .env are already resolved — skip Step 3."
echo ""
```

- [ ] **Step 7: Verify syntax**

```bash
bash -n install.sh && echo "SYNTAX_OK" || echo "SYNTAX_ERROR"
```

Expected: `SYNTAX_OK`

- [ ] **Step 8: Verify no legacy references**

```bash
grep -cE 'API_PORT|npm install|SmartHub API|Step 3b' install.sh
```

Expected: `0`

- [ ] **Step 9: Commit**

```bash
git add install.sh
git commit -m "infra: update install.sh for ha-mcp migration

Remove API port conflict resolution and API_PORT references.
Replace npm install with uv + ha-mcp installation.
Add MCP config for openclaw.json (native) or .claude/settings.json (bridge).
Update intro text and completion message."
```

---

### Task 4.2: Update tools/setup.md

**Files:**
- Modify: `tools/setup.md` (4 targeted edits)

- [ ] **Step 1: Delete Step 3b entirely (lines 74-127)**

Remove the entire "Step 3b: Check for Port Conflicts" section. This includes:
- The API port conflict resolution block
- The `grep -rn 'localhost:3001'` reference
- All content between the `## Step 3b` header and the `---` before Step 4

The HA port conflict resolution in install.sh is sufficient — no need for a separate Step 3b.

- [ ] **Step 2: Remove API_PORT references from Steps 4-7**

Scan Steps 4-7 (Docker setup, HA onboarding, token creation, .env setup) for any `API_PORT` references:

```bash
grep -n 'API_PORT' tools/setup.md
```

Remove or update any matches found in Steps 4-7. These may include:
- References to "enter your API port" in .env setup instructions
- `API_PORT` in the `.env` file template shown to the user
- Any mention of the SmartHub API in the Docker Compose step

If no matches exist in Steps 4-7, this step is a no-op.

- [ ] **Step 3: Replace Step 8 (lines 271-287)**

Old:
```markdown
## Step 8: Restart the API

The API container needs to pick up the new token:

```bash
docker compose restart api
```

Wait a few seconds, then verify:

```bash
API_PORT=$(grep API_PORT .env | cut -d= -f2)
curl -s http://localhost:${API_PORT}/api/health
```

Should return `{"status":"ok","ha_connected":true}`.
```

New:
```markdown
## Step 8: Verify ha-mcp Can Reach HA

ha-mcp is spawned on demand (no persistent service to restart). Verify it can connect:

```bash
HOMEASSISTANT_TOKEN=$(grep HA_TOKEN .env | cut -d= -f2) \
HOMEASSISTANT_URL=$(grep HA_URL .env | cut -d= -f2) \
uvx ha-mcp@7.2.0 --smoke-test
```

Expected success: "Connected to Home Assistant at <URL>."
Expected failure: error message indicating which component failed.

**Smoke-test fallback:** If `--smoke-test` does not exist in v7.2.0, use:
```bash
uvx ha-mcp@7.2.0 --help >/dev/null 2>&1 && echo "MCP_INSTALLED" || echo "MCP_MISSING"
```
This only verifies ha-mcp is installed (not HA connectivity). HA connectivity is confirmed by Step 4 (HA API poll in Step 4 of setup.md).
```

- [ ] **Step 4: Replace Step 9 (lines 290-303)**

Old:
```markdown
## Step 9: Verify Connection

Test that the full pipeline works:

```bash
API_PORT=$(grep API_PORT .env | cut -d= -f2)
curl -s http://localhost:${API_PORT}/api/devices
```

Tell the user what you find:

- If devices are returned → "Connected! I found X devices."
- If `{"devices":[],"count":0}` → "Connected, but no devices yet. We can add integrations next."
- If an error → troubleshoot based on the error message.
```

New:
```markdown
## Step 9: Verify Connection

Test that the full pipeline works by using `ha_search_entities` to list entities:

```
Tool: ha_search_entities
  query: ""
```

Tell the user what you find:

- If entities are returned → "Connected! I found X entities."
- If no entities → "Connected, but no devices yet. We can add integrations next."
- If an error → check `tools/_errors.md` for troubleshooting.
```

- [ ] **Step 5: Update Step 10 (lines 305-317)**

Old:
```markdown
> SmartHub is ready! Here's what we can do next:
```

New:
```markdown
> ha-mcp is connected! Here's what we can do next:
```

- [ ] **Step 6: Verify no legacy references**

```bash
grep -cE 'API_PORT|localhost:3001|docker compose restart api|SmartHub API|Step 3b' tools/setup.md
```

Expected: `0`

- [ ] **Step 7: Commit**

```bash
git add tools/setup.md
git commit -m "docs: update setup.md for ha-mcp migration

Delete Step 3b (API port conflicts — no longer needed).
Replace Step 8 API restart with ha-mcp smoke test.
Replace Step 9 curl verification with ha_search_entities.
Update completion message."
```

---

### Task 4.3: Update README.md

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Replace architecture diagram (lines 8-48)**

Replace the entire ASCII art diagram with:

```
  "Turn off the lights"         "Set AC to 24"         "I'm leaving for work"
          │                          │                          │
          └──────────────────────────┼──────────────────────────┘
                                     │
                                     ▼
                        ┌────────────────────────┐
                        │   Your Messaging App   │
                        │ (Discord, Telegram, …) │
                        └───────────┬────────────┘
                                    │
                                    ▼
                        ┌────────────────────────┐
                        │      OpenClaw          │
                        │   (AI agent, Claude)   │
                        │                        │
                        │  Reads skill files in  │
                        │  tools/ to know how    │
                        │  to control devices    │
                        └───────────┬────────────┘
                                    │
                                    │ MCP protocol (stdio)
                                    │
                        ┌────────────────────────┐
                        │       ha-mcp           │
                        │   (87 structured tools) │
                        │                        │
                        │  WebSocket to HA,      │
                        │  state verification,   │
                        │  tool search           │
                        └───────────┬────────────┘
                                    │
                                    ▼
                        ┌────────────────────────┐
                        │   Home Assistant        │
                        │      (Docker)           │
                        └───────────┬────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
                 Lights           AC/TV          Sensors
                Switches        Cameras         Cookers
```

- [ ] **Step 2: Update "What OpenClaw Sets Up" table (line 95)**

Old:
```markdown
| Start Home Assistant | Runs `docker compose up -d` to launch HA and the API |
```

New:
```markdown
| Start Home Assistant | Runs `docker compose up -d` to launch HA |
```

- [ ] **Step 3: Update Project Structure (lines 144-176)**

Replace the project structure tree:

```
home-assistant/
├── CLAUDE.md                    # Agent behavior rules (auto-loaded)
├── TOOLS.md                     # Skill router — maps devices to files
├── docker-compose.yml           # Runs Home Assistant
├── .env                         # HA token, timezone
├── .claude/
│   └── settings.json            # ha-mcp MCP server config (interim bridge)
│
├── tools/                       # Skill files — the agent's knowledge base
│   ├── _common.md               #   ha-mcp tool patterns, network info
│   ├── _ha-mcp.md               #   ha-mcp tool quick reference
│   ├── _errors.md               #   Error handling & recovery
│   ├── _services.md             #   Services by domain (light, climate, etc.)
│   ├── integrations/
│   │   └── _guide.md            #   Integration setup (HACS, config flows, OAuth)
│   ├── automations/
│   │   ├── _guide.md            #   Automation workflow & checklist
│   │   └── _reference.md        #   JSON schema, trigger/action types, templates
│   ├── xiaomi-home/
│   │   ├── _integration.md      #   Xiaomi setup, cloud regions, quirks
│   │   ├── tv.md                #   TV commands & quirks
│   │   ├── ma8-ac.md            #   AC commands & quirks
│   │   └── p1v2-cooker.md       #   Smart cooker commands & quirks
│   └── printer/
│       └── office-printer.md    #   CUPS printer setup
│
├── ha-config/                   # HA configuration (Docker volume)
└── docs/                        # Research, specs, design docs
```

- [ ] **Step 4: Update "How the Agent Finds Knowledge" diagram (lines 180-192)**

Old:
```markdown
CLAUDE.md (always loaded)
    │
    ├─ "Before controlling a device" ──→ reads tools/_common.md
    │                                     then reads device skill file
```

New:
```markdown
CLAUDE.md (always loaded)
    │
    ├─ "Before controlling a device" ──→ reads tools/_common.md for ha-mcp patterns
    │                                     then reads device skill file for commands
```

- [ ] **Step 5: Update Requirements section (lines 199-204)**

Old:
```markdown
- **Docker** — runs Home Assistant and the SmartHub API
```

New:
```markdown
- **Docker** — runs Home Assistant
- **uv** — Python package manager for running ha-mcp
```

- [ ] **Step 6: Remove HA troubleshooting SmartHub reference**

If there are any references to the SmartHub API in the Troubleshooting section, remove them. The HA troubleshooting curl command (`curl http://localhost:8123/api/`) stays — it checks HA directly, not the SmartHub API.

- [ ] **Step 7: Verify no legacy references**

```bash
grep -cE 'SmartHub API|Bun.*Elysia|API_PORT|api/.*src' README.md
```

Expected: `0`

- [ ] **Step 8: Commit**

```bash
git add README.md
git commit -m "docs: update README.md for ha-mcp architecture

Replace SmartHub API architecture diagram with ha-mcp.
Update project structure, requirements, and setup references."
```

---

## Phase 5: Cross-Cutting Verification

**Goal:** Verify no legacy SmartHub API references remain in any migrated file. This is the gate before the parallel run period.

**Parallelizable:** No — this is a single verification task.

### Task 5.1: Full-repo legacy reference scan

**Files:** All modified files from Phases 1–4

- [ ] **Step 1: Scan for API_PORT references (excluding api/ directory)**

```bash
grep -r 'API_PORT' --include='*.md' --include='*.yml' --include='*.json' --include='*.sh' . | grep -v '^./api/' | grep -v '^./docs/superpowers/'
```

Expected: No output. If any matches, fix them.

- [ ] **Step 2: Scan for SmartHub API references**

```bash
grep -r 'SmartHub API' --include='*.md' --include='*.sh' . | grep -v '^./api/' | grep -v '^./docs/superpowers/'
```

Expected: No output (the string "SmartHub" may appear in branding like "SmartHub — AI Smart Home" in CLAUDE.md and README.md — that's OK. Only "SmartHub API" references are legacy.)

- [ ] **Step 3: Scan for curl-to-API patterns**

```bash
grep -rE 'curl.*localhost:\$\{API_PORT\}|curl.*localhost:3001|/api/devices|/api/services.*curl|/api/health' --include='*.md' --include='*.sh' . | grep -v '^./api/' | grep -v '^./docs/superpowers/'
```

Expected: No output. Note: `curl -s ${HA_URL}/api/` is fine — that checks HA directly. Only curl to the SmartHub API is legacy.

- [ ] **Step 4: Scan for PI_IP in dashboard link generation**

```bash
grep -r 'PI_IP' --include='*.md' . | grep -v '^./api/' | grep -v '^./docs/superpowers/'
```

Expected: No output. Dashboard links should use `homeassistant.local`.

Exception: `tools/integrations/_guide.md` and `tools/setup.md` may still reference `hostname -I` for mDNS setup and OAuth fallback — those are infrastructure commands, not user-facing links, and are acceptable.

- [ ] **Step 5: Validate JSON configs**

```bash
python3 -c "import json; json.load(open('.claude/settings.json')); print('settings.json: VALID')"
```

- [ ] **Step 6: Validate docker-compose.yml**

```bash
docker compose config --quiet 2>&1 && echo "docker-compose: VALID" || echo "docker-compose: INVALID"
```

- [ ] **Step 7: Validate install.sh syntax**

```bash
bash -n install.sh && echo "install.sh: VALID" || echo "install.sh: INVALID"
```

- [ ] **Step 8: Commit any fixes found during verification**

If any legacy references were found and fixed:
```bash
git add -A
git commit -m "fix: remove remaining legacy SmartHub API references"
```

---

## Phase 6: Parallel Run & Cleanup (GATED)

**Goal:** Run ha-mcp alongside the old SmartHub API for at least one week, verify all endpoints have working ha-mcp equivalents, then remove `api/`.

**GATE:** This phase does NOT execute automatically. It requires:
1. At least one week of parallel operation
2. All verification checklist items passing
3. User confirmation before deleting `api/`

### Task 6.1: Parallel run verification

**Files:** None (verification only)

- [ ] **Step 1: Run the verification checklist**

| SmartHub API endpoint | ha-mcp equivalent | Test | Pass? |
|---|---|---|---|
| `GET /api/devices` | `ha_search_entities` | Search for `media_player.edgenesis_tv` (or known entity) | |
| `GET /api/devices/:id` | `ha_get_state` | Get state of a specific entity, verify attributes match | |
| `GET /api/areas` | `ha_get_areas` | List areas, verify count matches HA dashboard | |
| `POST /api/services/:domain/:service` | `ha_call_service` | Turn a light/switch on and off, verify via WebSocket state change | |
| `GET /api/camera/:entity_id/snapshot` | HA native `/api/camera_proxy/<entity_id>` | Verify camera snapshot accessible (if camera entities exist) | |
| Entity "unavailable" recovery | `ha_call_service` + WebSocket | Call service on "unavailable" entity (e.g., Xiaomi TV), verify it works | |

- [ ] **Step 2: Confirm all rows pass**

All applicable rows must pass. Camera test is skipped if no camera entities exist.

- [ ] **Step 3: Remove api/ directory (requires user confirmation)**

```bash
rm -rf api/
```

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "chore: remove SmartHub API server

All endpoints verified to have ha-mcp equivalents during parallel run.
Parallel run period: [start date] to [end date]."
```

- [ ] **Step 5: Verify clean state**

```bash
grep -r 'API_PORT' . --include='*.md' --include='*.yml' --include='*.json' --include='*.sh' | grep -v '^./docs/superpowers/'
```

Expected: No output.

---

## Appendix: ha-mcp Tool Call Syntax

All skill files use this consistent format for ha-mcp tool calls:

```markdown
```
Tool: <tool_name>
  param1: "value"
  param2: "value"
  data: {"key": "value"}
```
```

This is the LLM-facing syntax. ha-mcp tools are invoked via MCP protocol — the LLM reads this syntax from skill files and translates it into MCP tool calls automatically.

## Appendix: What's NOT in This Plan

Per the issue doc, these are explicitly out of scope:

- **`scripts/approval_gate.py`** — Layer 2 approval gating is blocked on research spike. Do not create this file.
- **OpenClaw native MCP config** — Tracked in openclaw/openclaw#4834. When it ships, move config from `.claude/settings.json` to `openclaw.json` under `mcp.servers`.
- **Public response to data exfiltration claims** — Marketing workstream.
- **Local model support via Ollama** — Feature workstream.
- **YAML-only export mode** — Feature workstream.
- **Automation audit/attribution log** — Feature workstream.
