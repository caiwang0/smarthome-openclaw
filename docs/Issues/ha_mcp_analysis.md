# ha-mcp — Competitive Analysis

Source: https://github.com/homeassistant-ai/ha-mcp
Version analyzed: v7.2.0 (April 2026)
Stars: 2,160 | Forks: 73 | License: MIT | Language: Python 3.13+

---

## What It Is

An MCP server (Model Context Protocol) that sits between any AI client and Home Assistant. It exposes 87 tools that let the AI read state, control devices, manage automations, edit dashboards, and more — all through a standardized protocol.

Unlike OpenClaw (which is a bot that embeds LLM orchestration), ha-mcp is a **dumb pipe with smart metadata**. It doesn't contain an LLM — it provides tools that any MCP-compatible AI client can call.

---

## Architecture

```
AI Client (Claude Desktop, ChatGPT, Cursor, Claude Code, etc.)
    ↕ MCP protocol (stdio / HTTP / SSE / OAuth)
ha-mcp server (built on FastMCP framework)
    ↕ REST API (httpx) + WebSocket (websockets)
Home Assistant instance
```

### Transport Modes

The same server code supports 4 transport modes via different entry points:

| Entry Point | Transport | Default Port | Use Case |
|---|---|---|---|
| `ha-mcp` | stdio (stdin/stdout) | — | Claude Desktop, local CLI tools |
| `ha-mcp-web` | HTTP (streamable) | 8086 | Web clients, Docker deployments |
| `ha-mcp-sse` | Server-Sent Events | 8087 | Legacy MCP clients |
| `ha-mcp-oauth` | HTTP + OAuth 2.1 | 8086 | Multi-user (claude.ai, shared servers) |

### Key Dependencies

- **FastMCP 3.2.0** — MCP server framework (handles protocol, transports, tool registration)
- **httpx 0.28.1** — Async HTTP client for HA REST API
- **websockets 16.0** — Real-time state monitoring
- **pydantic 2.12.5** — Settings validation, tool parameter schemas
- **python-dotenv** — Environment configuration

---

## Tool System (87 Tools)

### Organization

Tools live in `src/ha_mcp/tools/tools_*.py` files. A `ToolsRegistry` auto-discovers them at startup by scanning for files matching the `tools_*.py` pattern and calling their `register_*_tools()` function. Adding a new tool module requires zero changes to the registry.

### Tool Categories

| Category | Example Tools |
|---|---|
| Search & Discovery | `ha_search_entities`, `ha_deep_search`, `ha_get_overview`, `ha_get_state` |
| Service & Device Control | `ha_call_service`, `ha_bulk_control`, `ha_list_services` |
| Automations | `ha_config_get_automation`, `ha_config_set_automation`, `ha_config_remove_automation` |
| Scripts | `ha_config_get_script`, `ha_config_set_script`, `ha_config_remove_script` |
| Dashboards | `ha_config_get_dashboard`, `ha_config_set_dashboard`, `ha_config_delete_dashboard` |
| Helpers | `ha_config_list_helpers`, `ha_config_set_helper`, `ha_config_remove_helper` |
| HACS | `ha_hacs_search`, `ha_hacs_download`, `ha_hacs_add_repository` |
| History & Statistics | `ha_get_history`, `ha_get_statistics`, `ha_get_automation_traces` |
| System | `ha_backup_create`, `ha_backup_restore`, `ha_check_config`, `ha_restart` |
| Calendar | `ha_config_get_calendar_events`, `ha_config_set_calendar_event` |
| Areas & Floors | `ha_config_list_areas`, `ha_config_set_area`, `ha_config_list_floors` |
| Integrations | `ha_get_integration`, `ha_delete_config_entry` |
| Filesystem | `ha_list_files`, `ha_read_file`, `ha_write_file` (requires custom component) |
| YAML Config | `ha_config_set_yaml` (requires custom component + feature flag) |

### Tool Search Transform (Context Window Optimization)

With `ENABLE_TOOL_SEARCH=true`, the server replaces the full 87-tool catalog with:

1. **`ha_search_tools`** — BM25 keyword search over all tools (returns top 5 matches with descriptions and parameter schemas)
2. **`ha_call_read_tool`** — Proxy for read-only operations
3. **`ha_call_write_tool`** — Proxy for create/update operations
4. **`ha_call_delete_tool`** — Proxy for delete operations
5. **Pinned tools** — A small set of critical tools that remain always visible

This dramatically reduces idle context token usage. Each tool has annotations (`readOnlyHint`, `destructiveHint`) that route it to the correct proxy.

Additional BM25 tuning via `SearchKeywordsTransform` appends extra keywords to tool descriptions and overrides overly broad descriptions (e.g., narrowing `ha_deep_search` so it stops matching generic queries).

### Tool Annotations

Every tool is annotated with MCP annotations that AI clients can use for permission gating:

- `readOnlyHint: True` — Safe, no side effects
- `destructiveHint: True` — Creates, modifies, or deletes data

**Important**: These are hints — enforcement is client-side, not server-side.

---

## HA Communication Layer

### REST Client (`HomeAssistantClient`)

Standard async HTTP client using httpx, hitting HA's `/api/*` endpoints:

- Bearer token authentication
- Configurable timeout (default 30s) and retries (default 3)
- Structured error hierarchy: `HomeAssistantConnectionError`, `HomeAssistantAuthError`, `HomeAssistantAPIError`
- SOCKS proxy support for advanced network setups

### WebSocket Client

Persistent WebSocket connection to HA for real-time operations:

- **State change verification**: After calling a service (e.g., `light.turn_on`), waits for WebSocket to confirm the entity actually changed state. This is the `wait=True` parameter on `ha_call_service`.
- **Async operation monitoring**: `ha_get_operation_status` tracks long-running operations
- **Event handlers**: Registered callbacks for specific event types
- **Connection state management**: Handles auth handshake, reconnection, and message ID sequencing

### Custom Component (`ha_mcp_tools`)

A companion HA integration (installable via HACS) that extends HA's API with capabilities not available in the standard REST API:

| Tool | What It Does |
|---|---|
| `ha_config_set_yaml` | Add/replace/remove top-level YAML keys in `configuration.yaml` (with automatic backup and config validation) |
| `ha_list_files` | List files in allowed directories (`www/`, `themes/`, `custom_templates/`) |
| `ha_read_file` | Read files from allowed paths |
| `ha_write_file` | Write files to allowed directories |
| `ha_delete_file` | Delete files from allowed directories |

Gated behind feature flags: `HAMCP_ENABLE_FILESYSTEM_TOOLS=true` and `ENABLE_YAML_CONFIG_EDITING=true`.

---

## OAuth Mode (Multi-User)

### Flow

1. AI client discovers the MCP server and initiates OAuth 2.1 with PKCE
2. User is redirected to a **consent form** (not traditional OAuth — there's no HA identity provider integration)
3. User pastes their HA Long-Lived Access Token into the form
4. Token is encoded into a stateless OAuth access token (base64 JSON, HMAC-signed)
5. Each subsequent request extracts the HA token from OAuth claims and routes to the correct HA instance

### Key Design Decisions

- **Fully stateless tokens**: HA credentials are embedded in the token itself — no server-side session storage. Survives container restarts.
- **`OAuthProxyClient`**: A proxy that intercepts all client attribute access (`__getattr__`), extracts the OAuth token from the current request context, and forwards to a per-user `HomeAssistantClient`. Cached by token hash.
- **Dynamic Client Registration (DCR)**: MCP clients can register themselves automatically — no manual client ID setup.
- **HA URL is server-side config**: Only the token varies per user. Set `HOMEASSISTANT_URL` once, users provide only their token.

---

## Skills System

Bundled best-practice skills from `homeassistant-ai/skills` (git submodule) teach the AI agent HA-specific domain knowledge:

### How Skills Are Served

1. **MCP Resources** (`skill://` URIs): For clients that support MCP resources, skills are discoverable via `resources/list` and readable via `resources/read`. Powered by FastMCP's `SkillsDirectoryProvider`.

2. **Tools fallback** (`list_resources`/`read_resource`): For clients that don't support MCP resources (like claude.ai), skills are exposed as tools via FastMCP's `ResourcesAsTools` transform.

3. **Guidance tools** (`ha_get_skill_*`): One lightweight tool per skill, whose description contains the trigger conditions. This ensures AI clients see when to use a skill even if they don't read server instructions.

4. **Server instructions**: Skill descriptions are compiled into the FastMCP server's `instructions` field (for clients that support it).

### What Skills Cover

Skills contain domain knowledge like:
- When to use helpers vs templates
- How to structure automations correctly
- Proper use of automation modes
- Safe refactoring workflows
- Native constructs over Jinja2 workarounds

---

## Server Initialization

### Lazy Loading Pattern

The server uses aggressive lazy initialization for fast startup:

1. **Immediate** (fast): Settings loaded, FastMCP server created
2. **Lazy** (on first access): `HomeAssistantClient`, `SmartSearchTools`, `DeviceControlTools`
3. **Deferred** (at registration time): Tool modules are discovered at startup (filename scan only) but imported and registered later

### Startup Sequence

```
HomeAssistantSmartMCPServer.__init__()
  → get_global_settings()           # Load env vars
  → _build_skills_instructions()    # Compile skill descriptions
  → FastMCP(name, version, icons, instructions)
  → _initialize_server()
      → tools_registry.register_all_tools()   # Import + register all tool modules
      → register_enhanced_tools()              # Domain info helpers
      → _register_skills()                     # MCP resources + tools + guidance
      → _apply_tool_search()                   # BM25 search transform (optional)
```

---

## Configuration

All via environment variables (or `.env` file):

| Variable | Default | Description |
|---|---|---|
| `HOMEASSISTANT_URL` | (required) | HA instance URL |
| `HOMEASSISTANT_TOKEN` | (required) | Long-lived access token (`demo` for demo env) |
| `HA_TIMEOUT` | 30 | Request timeout (seconds) |
| `FUZZY_THRESHOLD` | 60 | Entity search fuzziness (0-100) |
| `ENABLE_WEBSOCKET` | true | Real-time state monitoring |
| `ENABLE_SKILLS` | true | Serve skills as MCP resources |
| `ENABLE_SKILLS_AS_TOOLS` | true | Expose skills via tools (for clients without resource support) |
| `ENABLE_TOOL_SEARCH` | false | Replace tool catalog with BM25 search |
| `ENABLE_YAML_CONFIG_EDITING` | false | Allow YAML config editing (requires custom component) |
| `ENABLED_TOOL_MODULES` | all | Filter which tool modules load (e.g., `automation`) |
| `MCP_SERVER_NAME` | ha-mcp | Server name in MCP protocol |
| `MCP_PORT` | 8086 | HTTP/OAuth server port |
| `MCP_SECRET_PATH` | /mcp | HTTP endpoint path |
| `MCP_BASE_URL` | (OAuth only) | Public URL for OAuth redirects |
| `LOG_LEVEL` | INFO | Logging verbosity |

---

## Deployment Options

1. **pip/uvx** — Direct Python install: `uvx ha-mcp`
2. **Docker** — `ghcr.io/homeassistant-ai/ha-mcp:latest`
3. **Home Assistant Add-on** — Native add-on, auto-connects to HA (no token needed)
4. **Binary** — PyInstaller-built binary for macOS/Windows/Linux

---

## Comparison with OpenClaw

| Aspect | ha-mcp | OpenClaw |
|---|---|---|
| **What it is** | MCP server (protocol adapter) | Bot with embedded LLM orchestration |
| **AI Client** | Any MCP-compatible client | Specific bot platform (Feishu, Discord) |
| **HA Communication** | Direct REST + WebSocket | Via custom API proxy |
| **Tool Count** | 87 structured tools with schemas | Skill files + dynamic API calls |
| **Device Knowledge** | Skills as MCP resources | Skill markdown files in `tools/` |
| **Multi-user** | OAuth 2.1 with per-user tokens | Single token in `.env` |
| **Approval Gating** | Tool annotations (client-enforced) | CLAUDE.md rules (LLM-enforced) |
| **Transport** | stdio, HTTP, SSE, OAuth | HTTP API only |
| **Target User** | Power users with AI desktop apps | Non-technical users via messaging |
| **Runs On** | User's machine (local) | Raspberry Pi (server) |
| **State Verification** | WebSocket-based (confirms state changed) | API polling |
| **Ecosystem** | Works with Claude, ChatGPT, Cursor, etc. | Tied to specific LLM provider |

### Where ha-mcp Is Stronger

- **Ecosystem reach**: Works with any MCP client — not locked to one AI provider
- **Tool coverage**: 87 tools with full parameter schemas vs. ad-hoc API calls
- **State verification**: WebSocket confirmation that commands actually worked
- **Multi-user**: Real OAuth 2.1 flow vs. shared single token
- **Context efficiency**: Tool search transform reduces token usage
- **HACS integration**: Native tool for browsing and installing community integrations

### Where OpenClaw Is Stronger

- **Accessibility**: Non-technical users interact via messaging (Feishu/Discord) — no MCP client setup needed
- **Device-specific knowledge**: Granular skill files per device model (e.g., Xiaomi TV quirks)
- **Guided setup**: Step-by-step onboarding flow for Raspberry Pi deployment
- **Conversation context**: Bot retains full conversation state; MCP tools are stateless
- **Opinionated guidance**: CLAUDE.md rules encode best practices the AI follows proactively

### The Approval Gating Gap (Reddit Concern)

ha-mcp uses **MCP tool annotations** (`readOnlyHint` / `destructiveHint`) to categorize read vs. write operations. AI clients can use these for permission gating, but enforcement is client-side — the server itself doesn't block anything.

OpenClaw uses **CLAUDE.md rules** ("never create an automation without showing a summary and waiting for explicit yes"). Enforcement is LLM-side — the agent follows instructions, but there's no protocol-level enforcement.

Neither has true server-side write protection. ha-mcp's approach is more structured (metadata the client can enforce programmatically). OpenClaw's approach is more flexible (natural language rules can cover edge cases annotations can't).

---

## Takeaways for OpenClaw

1. **MCP compatibility is table stakes** — ha-mcp works with every major AI client. OpenClaw is locked to whichever bot platform it integrates with. Consider exposing an MCP interface alongside the bot.

2. **Tool annotations for safety** — Structured read/write/delete annotations are more trustworthy than LLM instruction-following. Even if OpenClaw keeps its current architecture, labeling API calls with risk levels would help.

3. **WebSocket state verification** — ha-mcp confirms commands actually worked via WebSocket. OpenClaw should verify state changes after service calls rather than assuming success.

4. **Tool search transform** — With 87 tools, ha-mcp had to solve context window bloat. As OpenClaw's skill files grow, a similar search/filter mechanism will be needed.

5. **The skills overlap** — Both projects independently arrived at "teach the AI device-specific knowledge via markdown files." ha-mcp bundles `homeassistant-ai/skills` as MCP resources; OpenClaw has `tools/*.md`. The content is similar — the delivery mechanism differs.

6. **OAuth for multi-user** — If OpenClaw ever supports multiple households or users, ha-mcp's stateless token approach (credentials embedded in OAuth token, no server-side sessions) is worth studying.
