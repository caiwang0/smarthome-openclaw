# OpenClaw Phase 2A: Chat + Device Control — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an AI chat sidebar to the smart home dashboard powered by an OpenClaw gateway instance using Claude Code CLI as its agent backend. No Anthropic API key needed.

**Architecture:** New OpenClaw `smarthub` gateway (port 18790) → ACPX plugin → Claude Code CLI → calls existing Elysia API endpoints for HA control. Elysia API proxies chat to OpenClaw. Dashboard renders a chat sidebar.

**Tech Stack:** OpenClaw gateway, ACPX plugin, Claude Code CLI, Elysia/Bun, React 19, Tailwind CSS

**Spec:** `docs/superpowers/specs/2026-03-26-openclaw-integration-design.md`

**Branch:** `feature/openclaw-chat` (in worktree at `../home-assistant-openclaw`)

---

## File Structure

### New Files

| File | Responsibility |
|------|---------------|
| `~/.openclaw-smarthub/openclaw.json` | OpenClaw gateway config for smart home instance |
| `~/.config/systemd/user/openclaw-smarthub.service` | Systemd unit for auto-start |
| `CLAUDE.md` (project root) | Instructions for Claude Code: HA API endpoints, device control, known issues |
| `api/src/routes/chat.ts` | Thin proxy: forwards chat to OpenClaw gateway, streams response back |
| `dashboard/src/components/ChatPanel.tsx` | Chat sidebar container |
| `dashboard/src/components/ChatMessage.tsx` | Message bubble |
| `dashboard/src/components/ChatInput.tsx` | Input box |

### Modified Files

| File | Change |
|------|--------|
| `api/src/index.ts` | Mount chat proxy route |
| `dashboard/src/types.ts` | Add chat types |
| `dashboard/src/api.ts` | Add `sendChatMessage()` streaming function |
| `dashboard/src/App.tsx` | Add chat toggle button + ChatPanel sidebar (incremental edits) |

---

## Task 1: Branch + Worktree Setup

- [ ] **Step 1: Create feature branch in a git worktree**

```bash
cd /home/edgenesis/Downloads/home-assistant
git branch feature/openclaw-chat 2>/dev/null || true
git worktree add ../home-assistant-openclaw feature/openclaw-chat
```

All subsequent commands use `/home/edgenesis/Downloads/home-assistant-openclaw` as the working directory.

- [ ] **Step 2: Verify worktree**

```bash
cd /home/edgenesis/Downloads/home-assistant-openclaw
git branch --show-current
```

Expected: `feature/openclaw-chat`

---

## Task 2: OpenClaw SmartHub Gateway Setup

**Files:**
- Create: `~/.openclaw-smarthub/openclaw.json`
- Create: `~/.config/systemd/user/openclaw-smarthub.service`

- [ ] **Step 1: Install ACPX dependencies**

```bash
cd /usr/lib/node_modules/openclaw/extensions/acpx
sudo npm install --omit=dev --no-save acpx@0.1.16
```

Expected: acpx installed in the plugin's node_modules

- [ ] **Step 2: Create OpenClaw smarthub config**

Create the directory and config file:

```bash
mkdir -p ~/.openclaw-smarthub
```

Write `~/.openclaw-smarthub/openclaw.json`:

```json
{
  "meta": {
    "lastTouchedVersion": "2026.3.13",
    "lastTouchedAt": "2026-03-27T00:00:00.000Z"
  },
  "agents": {
    "defaults": {
      "model": {
        "primary": "anthropic/claude-sonnet-4-6"
      },
      "workspace": "/home/edgenesis/Downloads/home-assistant-openclaw",
      "timeoutSeconds": 120,
      "sandbox": {
        "mode": "off"
      }
    }
  },
  "tools": {
    "profile": "coding"
  },
  "commands": {
    "native": "auto",
    "nativeSkills": "auto",
    "restart": true
  },
  "session": {
    "dmScope": "per-channel-peer"
  },
  "cron": {
    "enabled": false
  },
  "channels": {},
  "gateway": {
    "port": 18790,
    "mode": "local",
    "bind": "loopback",
    "auth": {
      "mode": "token",
      "token": "smarthub-local-token-2026"
    },
    "http": {
      "endpoints": {
        "chatCompletions": {
          "enabled": true
        }
      }
    },
    "tailscale": {
      "mode": "off"
    }
  },
  "plugins": {
    "entries": {
      "acpx": {
        "enabled": true,
        "config": {
          "cwd": "/home/edgenesis/Downloads/home-assistant-openclaw",
          "permissionMode": "approve-all",
          "nonInteractivePermissions": "deny",
          "timeoutSeconds": 120
        }
      }
    }
  }
}
```

- [ ] **Step 3: Copy auth profiles from main instance**

```bash
mkdir -p ~/.openclaw-smarthub/agents/main/agent
cp ~/.openclaw/agents/main/agent/auth-profiles.json ~/.openclaw-smarthub/agents/main/agent/auth-profiles.json
```

- [ ] **Step 4: Create systemd service**

Write `~/.config/systemd/user/openclaw-smarthub.service`:

```ini
[Unit]
Description=OpenClaw SmartHub Gateway
After=network-online.target
Wants=network-online.target

[Service]
ExecStart=/usr/bin/node /usr/lib/node_modules/openclaw/dist/index.js gateway --profile smarthub --port 18790
Restart=always
RestartSec=5
TimeoutStopSec=30
TimeoutStartSec=30
SuccessExitStatus=0 143
KillMode=control-group
Environment=HOME=/home/edgenesis
Environment=TMPDIR=/tmp
Environment=PATH=/home/edgenesis/.bun/bin:/home/edgenesis/.local/bin:/home/edgenesis/.npm-global/bin:/home/edgenesis/bin:/home/edgenesis/.volta/bin:/home/edgenesis/.asdf/shims:/home/edgenesis/.nvm/current/bin:/home/edgenesis/.fnm/current/bin:/home/edgenesis/.local/share/pnpm:/usr/local/bin:/usr/bin:/bin
Environment=OPENCLAW_GATEWAY_PORT=18790
Environment=OPENCLAW_SYSTEMD_UNIT=openclaw-smarthub.service
Environment=OPENCLAW_SERVICE_MARKER=openclaw
Environment=OPENCLAW_SERVICE_KIND=gateway
Environment=OPENCLAW_SERVICE_VERSION=2026.3.13

[Install]
WantedBy=default.target
```

- [ ] **Step 5: Start the gateway**

```bash
systemctl --user daemon-reload
systemctl --user enable --now openclaw-smarthub.service
```

- [ ] **Step 6: Verify gateway is running**

```bash
sleep 5
curl -s http://localhost:18790/health
```

Expected: `{"ok":true,"status":"live"}`

- [ ] **Step 7: Test chat completions endpoint**

```bash
curl -s -X POST http://localhost:18790/v1/chat/completions \
  -H "Authorization: Bearer smarthub-local-token-2026" \
  -H "Content-Type: application/json" \
  -d '{"model":"openclaw:main","messages":[{"role":"user","content":"Say hello in one word"}],"stream":false}' | head -50
```

Expected: JSON response with a completion containing "Hello" or similar

---

## Task 3: CLAUDE.md for Smart Home Context

**Files:**
- Create: `/home/edgenesis/Downloads/home-assistant-openclaw/CLAUDE.md`

This file tells Claude Code how to interact with the smart home system.

- [ ] **Step 1: Write CLAUDE.md**

```markdown
# SmartHub — AI Smart Home Assistant

You are OpenClaw, an AI assistant for a smart home hub powered by Home Assistant.
You help users control their devices, check status, and manage their smart home.

## How to Interact with Home Assistant

All device control goes through the SmartHub API running at `http://localhost:3001`.
Use `curl` commands to call these endpoints.

### List all devices
```bash
curl -s http://localhost:3001/api/devices | jq '.devices[] | {name, device_type, status, area_name, primary_entity}'
```

### Get a specific device
```bash
curl -s http://localhost:3001/api/devices/<device_id>
```

### Control a device (call a service)
```bash
curl -s -X POST http://localhost:3001/api/services/<domain>/<service> \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "<entity_id>"}'
```

Common services:
- `light/turn_on` — turn on a light (optional: `"brightness": 0-255`)
- `light/turn_off` — turn off a light
- `switch/turn_on` / `switch/turn_off` — toggle a switch
- `climate/set_temperature` — set thermostat (data: `"temperature": 24`)
- `climate/set_hvac_mode` — set mode (data: `"hvac_mode": "cool"`)
- `media_player/turn_off` — turn off media player
- `media_player/volume_up` / `media_player/volume_down`
- `media_player/media_play` / `media_player/media_pause`

### List areas/rooms
```bash
curl -s http://localhost:3001/api/areas | jq '.areas'
```

## Rules
- Be concise and friendly. Keep responses short (1-3 sentences for simple actions).
- After controlling a device, confirm what you did.
- If a device is offline, mention it and suggest the user check if it's powered on.
- Match the user's language — if they write in Chinese, respond in Chinese.
- Do NOT make up device names. Always check `/api/devices` first if unsure.
- When listing devices, format them as a readable list, not raw JSON.

## Known Issues
- Xiaomi TV (DLNA) frequently shows as "unavailable" but still accepts commands. Try the command anyway.
- TV cannot be powered on via network when in standby (Wi-Fi disconnects). This requires an IR blaster (Phase 3).
- OAuth integrations (Xiaomi Home) require the user to complete login in their browser.
```

- [ ] **Step 2: Commit**

```bash
cd /home/edgenesis/Downloads/home-assistant-openclaw
git add CLAUDE.md
git commit -m "feat: add CLAUDE.md with HA API instructions for OpenClaw agent"
```

---

## Task 4: Chat Proxy Route

**Files:**
- Create: `api/src/routes/chat.ts`
- Modify: `api/src/index.ts`

The chat route proxies requests to the OpenClaw gateway and streams the response back.

- [ ] **Step 1: Create the chat proxy route**

```typescript
// api/src/routes/chat.ts
import { Elysia } from "elysia";

const OPENCLAW_URL = process.env.OPENCLAW_URL || "http://localhost:18790";
const OPENCLAW_TOKEN = process.env.OPENCLAW_TOKEN || "smarthub-local-token-2026";

export const chatRoutes = new Elysia()
  .post("/api/chat", async ({ body }) => {
    const { message } = body as { message?: string };

    if (!message || typeof message !== "string" || !message.trim()) {
      return new Response(
        JSON.stringify({ error: "Message is required" }),
        { status: 400, headers: { "Content-Type": "application/json" } }
      );
    }

    try {
      const response = await fetch(`${OPENCLAW_URL}/v1/chat/completions`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${OPENCLAW_TOKEN}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          model: "openclaw:main",
          messages: [{ role: "user", content: message.trim() }],
          stream: true,
        }),
      });

      if (!response.ok || !response.body) {
        return new Response(
          JSON.stringify({ error: "OpenClaw is offline or returned an error" }),
          { status: 502, headers: { "Content-Type": "application/json" } }
        );
      }

      // Pipe the SSE stream directly from OpenClaw to the client
      return new Response(response.body, {
        headers: {
          "Content-Type": "text/event-stream",
          "Cache-Control": "no-cache",
          "Connection": "keep-alive",
        },
      });
    } catch (err: any) {
      console.error("OpenClaw proxy error:", err.message);
      return new Response(
        JSON.stringify({ error: "OpenClaw is offline. Check that the gateway is running." }),
        { status: 502, headers: { "Content-Type": "application/json" } }
      );
    }
  });
```

- [ ] **Step 2: Mount the route in index.ts**

Add to `api/src/index.ts`:

```typescript
import { chatRoutes } from "./routes/chat";
```

Add `.use(chatRoutes)` after `.use(cameraRoutes)`.

- [ ] **Step 3: Verify API compiles**

```bash
cd /home/edgenesis/Downloads/home-assistant-openclaw/api
OPENCLAW_URL=http://localhost:18790 HA_URL=http://localhost:8123 HA_TOKEN=test API_PORT=3099 timeout 5 bun run src/index.ts 2>&1 || true
```

Expected: prints `API running on port 3099`

- [ ] **Step 4: Commit**

```bash
cd /home/edgenesis/Downloads/home-assistant-openclaw
git add api/src/routes/chat.ts api/src/index.ts
git commit -m "feat: add /api/chat proxy route to OpenClaw gateway"
```

---

## Task 5: Dashboard Chat Types & API Client

**Files:**
- Modify: `dashboard/src/types.ts`
- Modify: `dashboard/src/api.ts`

- [ ] **Step 1: Add chat types to types.ts**

Append to `dashboard/src/types.ts`:

```typescript
// ---- Chat Types ----

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  isStreaming?: boolean;
}
```

- [ ] **Step 2: Add streaming chat function to api.ts**

Update the import at line 1 to include `ChatMessage`:

Change `import type { DevicesResponse, AreasResponse } from "./types";`
to `import type { DevicesResponse, AreasResponse, ChatMessage } from "./types";`

Then append to the end of `dashboard/src/api.ts`:

```typescript
export async function sendChatMessage(
  message: string,
  onText: (text: string) => void,
  onDone: () => void,
  onError: (error: string) => void
): Promise<void> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ error: "Request failed" }));
    onError(body.error || `Chat request failed: ${res.status}`);
    return;
  }

  if (!res.body) {
    onError("No response body");
    return;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const data = line.slice(6).trim();
      if (data === "[DONE]") {
        onDone();
        return;
      }
      try {
        const parsed = JSON.parse(data);
        const delta = parsed.choices?.[0]?.delta?.content;
        if (delta) onText(delta);
      } catch {
        // Skip malformed events
      }
    }
  }
  onDone();
}
```

- [ ] **Step 3: Verify dashboard compiles**

```bash
cd /home/edgenesis/Downloads/home-assistant-openclaw/dashboard
npx tsc --noEmit 2>&1 | head -20
```

- [ ] **Step 4: Commit**

```bash
cd /home/edgenesis/Downloads/home-assistant-openclaw
git add dashboard/src/types.ts dashboard/src/api.ts
git commit -m "feat: add chat types and streaming API client for OpenClaw"
```

---

## Task 6: Chat UI Components

**Files:**
- Create: `dashboard/src/components/ChatMessage.tsx`
- Create: `dashboard/src/components/ChatInput.tsx`
- Create: `dashboard/src/components/ChatPanel.tsx`

- [ ] **Step 1: Create ChatMessage**

```tsx
// dashboard/src/components/ChatMessage.tsx
import type { ChatMessage as ChatMessageType } from "../types";

export default function ChatMessage({ message }: { message: ChatMessageType }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] px-3 py-2 text-sm font-mono ${
          isUser
            ? "bg-[#BFFF00] text-[#0A0A0A] rounded-t-lg rounded-bl-lg"
            : "bg-[#1A1A1A] text-[#E8E8E8] border border-[#2A2A2A] rounded-t-lg rounded-br-lg"
        }`}
      >
        <p className="whitespace-pre-wrap break-words">{message.content}</p>
        {message.isStreaming && (
          <span className="inline-block w-2 h-4 bg-[#BFFF00] animate-pulse ml-0.5" />
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Create ChatInput**

```tsx
// dashboard/src/components/ChatInput.tsx
import { useState } from "react";

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled: boolean;
}

export default function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [value, setValue] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2 p-3 border-t border-[#2A2A2A]">
      <input
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        placeholder={disabled ? "Thinking..." : "Ask OpenClaw..."}
        className="flex-1 bg-[#1A1A1A] border border-[#3A3A3A] text-[#E8E8E8] text-sm font-mono px-3 py-2 rounded focus:outline-none focus:border-[#BFFF00] disabled:opacity-50 placeholder:text-[#4A4A4A]"
      />
      <button
        type="submit"
        disabled={disabled || !value.trim()}
        className="px-3 py-2 bg-[#BFFF00] text-[#0A0A0A] text-sm font-mono font-bold uppercase tracking-wider rounded hover:bg-[#D4FF33] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
      >
        Send
      </button>
    </form>
  );
}
```

- [ ] **Step 3: Create ChatPanel**

```tsx
// dashboard/src/components/ChatPanel.tsx
import { useState, useRef, useEffect, useCallback } from "react";
import type { ChatMessage as ChatMessageType } from "../types";
import { sendChatMessage } from "../api";
import ChatMessage from "./ChatMessage";
import ChatInput from "./ChatInput";

const WELCOME_MESSAGE: ChatMessageType = {
  id: "welcome",
  role: "assistant",
  content:
    "Hi! I'm OpenClaw. I can control your devices and help manage your smart home. Try:\n\n" +
    '- "What devices do I have?"\n' +
    '- "Turn off the living room lights"\n' +
    '- "What\'s the temperature?"',
};

export default function ChatPanel() {
  const [messages, setMessages] = useState<ChatMessageType[]>([WELCOME_MESSAGE]);
  const [streaming, setStreaming] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = useCallback(async (text: string) => {
    const userMsg: ChatMessageType = {
      id: crypto.randomUUID(),
      role: "user",
      content: text,
    };

    const assistantId = crypto.randomUUID();
    const assistantMsg: ChatMessageType = {
      id: assistantId,
      role: "assistant",
      content: "",
      isStreaming: true,
    };

    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setStreaming(true);

    function updateAssistant(updater: (msg: ChatMessageType) => ChatMessageType) {
      setMessages((prev) =>
        prev.map((m) => (m.id === assistantId ? updater(m) : m))
      );
    }

    try {
      await sendChatMessage(
        text,
        (delta) => {
          updateAssistant((m) => ({ ...m, content: m.content + delta }));
        },
        () => {
          updateAssistant((m) => ({ ...m, isStreaming: false }));
          setStreaming(false);
        },
        (error) => {
          updateAssistant((m) => ({
            ...m,
            content: m.content || error,
            isStreaming: false,
          }));
          setStreaming(false);
        }
      );
    } catch {
      updateAssistant((m) => ({
        ...m,
        content: m.content || "Connection failed. Is the API running?",
        isStreaming: false,
      }));
      setStreaming(false);
    }
  }, []);

  return (
    <div className="flex flex-col h-full bg-[#0A0A0A] border-l border-[#2A2A2A]">
      <div className="px-3 py-3 border-b border-[#2A2A2A]">
        <div className="flex items-center justify-between">
          <span className="text-xs font-mono font-bold uppercase tracking-[0.15em] text-[#BFFF00]">
            OpenClaw
          </span>
          <span className="text-[10px] font-mono text-[#4A4A4A] uppercase">
            AI Assistant
          </span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {messages.map((msg) => (
          <ChatMessage key={msg.id} message={msg} />
        ))}
        <div ref={messagesEndRef} />
      </div>

      <ChatInput onSend={handleSend} disabled={streaming} />
    </div>
  );
}
```

- [ ] **Step 4: Verify dashboard compiles**

```bash
cd /home/edgenesis/Downloads/home-assistant-openclaw/dashboard
npx tsc --noEmit 2>&1 | head -20
```

- [ ] **Step 5: Commit**

```bash
cd /home/edgenesis/Downloads/home-assistant-openclaw
git add dashboard/src/components/ChatMessage.tsx dashboard/src/components/ChatInput.tsx dashboard/src/components/ChatPanel.tsx
git commit -m "feat: add ChatPanel, ChatMessage, and ChatInput components"
```

---

## Task 7: App.tsx Integration

**Files:**
- Modify: `dashboard/src/App.tsx`

Make **incremental edits** only. Do NOT replace the whole file.

- [ ] **Step 1: Add import and state**

Add import at the top:
```tsx
import ChatPanel from "./components/ChatPanel";
```

Add state inside `App()` function, after existing `useState` calls:
```tsx
const [chatOpen, setChatOpen] = useState<boolean>(() => {
  return localStorage.getItem("openclaw_chat_open") === "true";
});

function toggleChat() {
  setChatOpen((prev) => {
    const next = !prev;
    localStorage.setItem("openclaw_chat_open", String(next));
    return next;
  });
}
```

- [ ] **Step 2: Add toggle button to header**

Inside the `<header>`, wrap existing title content in a flex container and add toggle button.

After the opening `<header>` tag, add:
```tsx
<div className="flex items-center justify-between">
  <div>
```

After the device count `</p>`, close the wrappers and add button:
```tsx
  </div>
  <button
    onClick={toggleChat}
    className={`px-3 py-1.5 text-xs font-mono font-bold uppercase tracking-wider border transition-colors ${
      chatOpen
        ? "bg-[#BFFF00] text-[#0A0A0A] border-[#BFFF00]"
        : "bg-transparent text-[#6B6B6B] border-[#3A3A3A] hover:border-[#BFFF00] hover:text-[#BFFF00]"
    }`}
  >
    {chatOpen ? "Close Chat" : "OpenClaw"}
  </button>
</div>
```

- [ ] **Step 3: Add sidebar layout**

On the outermost `<div>` (the `min-h-screen` one), add `flex` to className.

Wrap all existing content (header + main) in:
```tsx
<div className={`flex-1 min-w-0 ${chatOpen ? "mr-[360px]" : ""}`}>
  {/* ...existing header and main... */}
</div>
```

After that wrapper, add:
```tsx
{chatOpen && (
  <div className="fixed top-0 right-0 w-[360px] h-screen z-50">
    <ChatPanel />
  </div>
)}
```

- [ ] **Step 4: Verify dashboard compiles and builds**

```bash
cd /home/edgenesis/Downloads/home-assistant-openclaw/dashboard
npx tsc --noEmit && npm run build 2>&1 | tail -5
```

Expected: no errors, build succeeds

- [ ] **Step 5: Commit**

```bash
cd /home/edgenesis/Downloads/home-assistant-openclaw
git add dashboard/src/App.tsx
git commit -m "feat: integrate ChatPanel sidebar with toggle in dashboard header"
```

---

## Task 8: End-to-End Verification

**Prerequisites:** HA running, OpenClaw smarthub gateway running (port 18790), Elysia API running

- [ ] **Step 1: Verify OpenClaw gateway health**

```bash
curl -s http://localhost:18790/health
```

Expected: `{"ok":true,"status":"live"}`

- [ ] **Step 2: Start Elysia API**

```bash
cd /home/edgenesis/Downloads/home-assistant-openclaw/api
API_PORT=3099 bun run src/index.ts &
sleep 3
```

- [ ] **Step 3: Test chat proxy with curl**

```bash
curl -N -X POST http://localhost:3099/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Say hello"}' 2>&1 | head -20
```

Expected: SSE stream with OpenAI-compatible chunks

- [ ] **Step 4: Test device query via chat**

```bash
curl -N -X POST http://localhost:3099/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What devices do I have?"}' 2>&1 | head -50
```

Expected: Claude Code calls `/api/devices` and returns a formatted device list

- [ ] **Step 5: Test empty message rejection**

```bash
curl -s -X POST http://localhost:3099/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": ""}'
```

Expected: `{"error":"Message is required"}` with status 400

- [ ] **Step 6: Build and test dashboard**

```bash
cd /home/edgenesis/Downloads/home-assistant-openclaw/dashboard
npm run build
```

Open dashboard in browser and verify:
- OpenClaw button appears in header
- Clicking opens the chat sidebar
- Sending "What devices do I have?" returns a device list
- Text streams incrementally
- Send button disabled when input is empty
- Input disabled while streaming
- Toggle state persists across page refreshes

- [ ] **Step 7: Final commit**

```bash
cd /home/edgenesis/Downloads/home-assistant-openclaw
git status
git add -A
git commit -m "feat: OpenClaw Phase 2A complete — AI chat with device control via Claude Code"
```
