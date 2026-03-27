# OpenClaw Integration Design Spec

**Date:** 2026-03-27 (revised)
**Author:** Claude (brainstorming session with user)
**Status:** Approved

## Goal

Integrate OpenClaw (with Claude Code CLI as its agent backend) into the smart home dashboard as a chat sidebar. Users can control devices, query status, and manage their smart home through natural language — without needing a separate Anthropic API key.

## Architecture

A new OpenClaw gateway instance (`smarthub` profile) runs on the Pi alongside the existing one. It uses the **ACPX plugin** to spawn Claude Code CLI as its agent backend. The Elysia API proxies chat requests to the OpenClaw gateway. Claude Code reads a project `CLAUDE.md` for HA-specific instructions and calls the existing Elysia API endpoints to interact with Home Assistant.

```
Dashboard (React)         Elysia API (Bun)         OpenClaw Gateway        Claude Code CLI
┌──────────┬──────┐      ┌───────────────┐        ┌──────────────┐       ┌──────────────┐
│ Device   │ Chat │─────▶│ /api/chat     │───────▶│ :18790       │──────▶│ claude CLI   │
│ Grid     │Panel │◀─────│ (proxy)       │◀───────│ /v1/chat/    │◀──────│ (ACPX)       │
│(existing)│(new) │stream│               │ stream │ completions  │       │              │
└──────────┴──────┘      │ /api/devices  │        └──────────────┘       │ reads        │
                         │ /api/services │                                │ CLAUDE.md    │
                         │ (existing)    │◀───────────────────────────────│ calls /api/* │
                         └───────────────┘                                └──────────────┘
                                │
                                ▼
                         ┌──────────────┐
                         │ Home         │
                         │ Assistant    │
                         └──────────────┘
```

**Key principle:** OpenClaw + Claude Code handle ALL AI/agent logic (conversation management, tool execution, reasoning). The Elysia API is just a proxy for chat and existing device/service endpoints.

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Agent Runtime | OpenClaw gateway (`smarthub` profile) with ACPX plugin |
| LLM Backend | Claude Code CLI (uses existing Claude Code auth on Pi — no separate API key) |
| Chat Proxy | Existing Elysia/Bun API (thin proxy to OpenClaw `/v1/chat/completions`) |
| HA Communication | Existing Elysia API endpoints (`/api/devices`, `/api/services/:domain/:service`, `/api/areas`) — called by Claude Code via HTTP |
| Frontend | React chat panel (new component) |
| Streaming | OpenAI-compatible SSE from OpenClaw gateway, proxied through Elysia |

## How Claude Code Interacts with HA

Claude Code doesn't call HA APIs directly. Instead, it calls the **existing Elysia API endpoints** via HTTP (using its built-in Bash/fetch tools):

| Action | Claude Code calls |
|--------|------------------|
| List devices | `curl http://localhost:3001/api/devices` |
| Get device status | `curl http://localhost:3001/api/devices/:id` |
| Control device | `curl -X POST http://localhost:3001/api/services/:domain/:service -d '{"entity_id":"..."}' ` |
| List areas | `curl http://localhost:3001/api/areas` |

These instructions are provided via a `CLAUDE.md` file in the project workspace that the ACPX plugin's `cwd` points to. No custom tool definitions or MCP servers needed for Phase 2A.

## OpenClaw Gateway Setup

### Profile: `smarthub`

Config location: `~/.openclaw-smarthub/openclaw.json`

Key settings:
- **Port:** 18790 (avoids conflict with main gateway on 18789)
- **ACPX plugin:** Enabled with `permissionMode: "approve-all"`, `cwd` pointing to project workspace
- **Gateway auth:** Token-based (loopback only — not exposed externally)
- **Channels:** No Discord/Telegram — HTTP-only for dashboard access
- **Model:** Uses Claude Code via ACPX (not direct Anthropic API)

### Systemd Service

`~/.config/systemd/user/openclaw-smarthub.service` — auto-starts on boot, restarts on failure.

## API Design

### Chat Proxy Endpoint

```
POST /api/chat
Request:  { message: string }
Response: Streaming text (proxied from OpenClaw's OpenAI-compatible SSE response)
```

The Elysia chat route:
1. Receives user message
2. Forwards to `http://localhost:18790/v1/chat/completions` as an OpenAI-compatible request
3. Streams the response back to the dashboard

OpenClaw handles conversation management internally (session-based). No conversation store needed in Elysia.

## Dashboard Chat Panel

### Layout

Right sidebar, collapsible via toggle button in header. Same as previous spec.

### Components

| Component | Responsibility |
|-----------|---------------|
| `ChatPanel` | Container: message list + input + toggle state |
| `ChatMessage` | Single message bubble (user or assistant) |
| `ChatInput` | Text input with send button, disabled while streaming |

### Behavior

- **Toggle:** Button in dashboard header shows/hides sidebar. State persisted in localStorage.
- **Streaming:** Reads SSE chunks from the proxied OpenAI-compatible response. Text appears incrementally.
- **Welcome message:** Hard-coded on first open: "Hi! I'm OpenClaw. I can control your devices and help manage your smart home."
- **Error handling:** If OpenClaw gateway is unreachable, display "OpenClaw is offline. Check that the gateway is running."

## Implementation Phases

### Phase 2A: Chat + Device Control (this phase)

**New files:**
- `api/src/routes/chat.ts` — thin proxy to OpenClaw gateway
- `dashboard/src/components/ChatPanel.tsx` — chat sidebar
- `dashboard/src/components/ChatMessage.tsx` — message bubble
- `dashboard/src/components/ChatInput.tsx` — input box
- `CLAUDE.md` — HA-specific instructions for Claude Code (API endpoints, device control commands, known issues)
- `~/.openclaw-smarthub/openclaw.json` — gateway config
- `~/.config/systemd/user/openclaw-smarthub.service` — systemd unit

**Modified files:**
- `api/src/index.ts` — mount chat proxy route
- `dashboard/src/App.tsx` — add chat toggle + ChatPanel (incremental edits)
- `dashboard/src/api.ts` — add `sendChatMessage()` streaming function
- `dashboard/src/types.ts` — add chat types

**Success criteria:**
- [ ] OpenClaw `smarthub` gateway starts and responds to health checks on port 18790
- [ ] Chat panel opens/closes via header toggle button; state persists across page refreshes
- [ ] User sends "What devices do I have?" → Claude Code calls Elysia `/api/devices` → responds with device list
- [ ] User sends "Turn off the living room lights" → Claude Code calls `/api/services/light/turn_off` → confirms
- [ ] Streaming works: text appears incrementally, not as a single block
- [ ] Input disabled while streaming; empty messages rejected client-side
- [ ] When OpenClaw gateway is down, user sees friendly error message

### Phase 2B & 2C (future)

Same scope as before (setup/discovery, troubleshooting). Claude Code can call HA REST API endpoints directly for config flows, diagnostics, etc. — just add instructions to `CLAUDE.md`.

## Error Handling

- **OpenClaw gateway down:** Elysia proxy returns `{ error: "OpenClaw is offline" }` with status 502.
- **Claude Code errors:** OpenClaw returns error in OpenAI-compatible format; proxy forwards it.
- **Streaming breaks:** Proxy closes the response; frontend shows "Response interrupted."

## Security Considerations

- **No API keys in `.env`:** Claude Code uses its own auth (already configured on the Pi). No secrets to manage.
- **Gateway auth:** OpenClaw gateway token is localhost-only. Not exposed to the network.
- **Tool boundaries:** Claude Code can only call the Elysia API (localhost:3001). ACPX `permissionMode: "approve-all"` allows autonomous tool execution.

## What Was Removed (vs. previous spec)

| Removed | Why |
|---------|-----|
| `@anthropic-ai/sdk` dependency | Claude Code CLI replaces direct API calls |
| `api/src/agent/conversation.ts` | OpenClaw manages conversations internally |
| `api/src/agent/system-prompt.ts` | `CLAUDE.md` replaces dynamic system prompt injection |
| `api/src/agent/tools.ts` | Claude Code uses Bash/fetch to call Elysia API — no custom tool definitions |
| `ANTHROPIC_API_KEY` in `.env` | Not needed — Claude Code has its own auth |
| Custom tool-use loop | OpenClaw + ACPX handles the agentic loop |

## Out of Scope (Future)

- Messaging app connectors (WhatsApp/Telegram/Discord) — add as OpenClaw channels later
- Automation creation from natural language
- MCP servers for direct HA WebSocket access (Phase 2B may add these)
- Voice input
