# SmartHub — AI-Powered Smart Home

Control your Home Assistant with natural language through any messaging app supported by OpenClaw (Discord, Telegram, WhatsApp, Feishu, and more). Powered by OpenClaw.

## How It Works

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
                        │       ha-mcp 7.2.0     │
                        │  (~90 structured tools)│
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

Say "I'm leaving for work" and OpenClaw turns off lights, sets the AC to eco, and confirms what it did.

---

## Quick Install

**Already have OpenClaw running?** Just tell your bot:

> Run this: `curl -fsSL https://raw.githubusercontent.com/caiwang0/smarthome-openclaw/main/install.sh -o /tmp/smarthub-install.sh && bash /tmp/smarthub-install.sh`

OpenClaw will install everything and walk you through setup automatically.

---

## Full Setup

Three manual steps, then OpenClaw guides you through everything else.

### 1. Install OpenClaw

**macOS / Linux:**

```bash
curl -fsSL https://openclaw.ai/install.sh | bash -s -- --beta
```

**Windows:**

```powershell
powershell -c "irm https://openclaw.ai/install.ps1 | iex"
```

### 2. Set Up OpenClaw with a Messaging App

Follow the [OpenClaw Getting Started guide](https://docs.openclaw.ai/start/getting-started) to connect a bot to your messaging app (Discord, Telegram, WhatsApp, Feishu, etc.) and point it at this repo.

Once the bot comes online, say: **"Help me set up SmartHub"**

---

## What OpenClaw Sets Up For You

| Step | What happens |
|------|-------------|
| Install Docker | Checks if Docker is installed, gives you the command if not |
| Start Home Assistant | Runs `docker compose up -d` to launch HA |
| HA onboarding | Tells you to open the browser, create your admin user |
| Access token | Guides you to create a long-lived token and paste it in chat |
| Configure .env | Writes the token and verifies the connection |
| Add integrations | Walks you through adding Xiaomi, Philips Hue, or any other brand |
| Discover devices | Shows what devices were found after each integration |
| Remote access *(optional)* | Sets up a Cloudflare Tunnel so you can reach HA from anywhere |

### Example Conversation

```
You:      Help me set up SmartHub
OpenClaw: Let's get your smart home running. Do you have Docker installed?
          Run: docker --version

You:      Docker version 27.5.1
OpenClaw: Docker is ready. Starting Home Assistant...
          Done. Open http://homeassistant.local:8123 in your browser.
          Create your admin account and let me know when you're done.

You:      Done, created user "alice"
OpenClaw: Now go to your profile → Security → Long-Lived Access Tokens
          → Create Token. Name it "openclaw" and paste it here.

You:      eyJhbGciOiJIUzI1NiIs...
OpenClaw: Saved. Connection verified — Home Assistant 2026.3.4, 0 devices.
          Want to add your first device integration?
```

---

## After Setup

Talk to OpenClaw naturally:

| You say | What happens |
|---------|-------------|
| "Turn off the living room lights" | Controls the device via HA |
| "Set the AC to 24" | Calls the climate service |
| "I'm leaving for work" | Turns off lights, sets AC to eco, locks doors |
| "Why is the bedroom so hot?" | Checks sensors, AC state, diagnoses the issue |
| "What devices do I have?" | Lists all connected devices by room |
| "Turn off the TV at 3pm every day" | Creates an automation |
| "Add Xiaomi Home" | Walks you through the integration setup |

---

## Safety

Destructive actions are protected by **two layers**:

1. **`CLAUDE.md` rule** — the agent is told to show you a summary and wait for an explicit "yes" before any persistent change. A soft hint; the model usually follows it, but can rationalize past it under pressure.
2. **`scripts/approval-gate.py` hook** — a Claude Code PreToolUse hook that reads your latest message and **denies the call unless it contains an affirmative** (`yes`, `confirm`, `ok`, `好`, `sí`, `はい`, …). Deterministic — fires regardless of model or permission mode.

**What's gated:**

| Category | Examples |
|----------|----------|
| Automations & Scripts | create, modify, delete |
| Integrations | add, remove, enable/disable |
| Devices | remove, rename, update |
| System | restart, reload core, backup restore |
| HACS | add repository, download |

Non-destructive actions (turning on lights, setting AC, reading state) run without confirmation — only changes that persist across restarts are gated.

**How it works:** The hook is wired in `.claude/settings.json` to match the destructive tool names above. On each matched call, it reads the conversation transcript, pulls your last message, and checks it against the affirmative patterns. No match → deny → the agent has to show a summary and ask first.

**Example — creating an automation:**

![Confirmation flow in Discord](docs/example-review.png)

The agent shows a summary, waits for "yes", then executes. Skip the "yes" and the hook blocks the call.

---

## Project Structure

```
home-assistant/
├── CLAUDE.md                    # Agent behavior rules (auto-loaded)
├── TOOLS.md                     # Skill router — maps devices to files
├── docker-compose.yml           # Runs Home Assistant
├── install.sh                   # One-command installer (clone, port-resolve, wire ha-mcp)
├── .env.example                 # Template — copy to .env, fill in HA_TOKEN
├── .claude/
│   └── settings.json            # ha-mcp MCP server + PreToolUse approval hook
│
├── scripts/
│   └── approval-gate.py         # Blocks destructive ha-mcp calls unless the user
│                                # explicitly confirmed in their latest message
│
├── tools/                       # Skill files — the agent's knowledge base
│   ├── setup.md                 #   First-run setup flow (Docker → HA → token → .env)
│   ├── _common.md               #   ha-mcp tool patterns, network info
│   ├── _errors.md               #   Error handling & recovery
│   ├── _services.md             #   Domain quirks (HVAC modes, brightness 0-255, etc.)
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
├── ha-config/                   # HA configuration (Docker volume, gitignored)
└── docs/                        # Research, specs, design docs
```

### How the Agent Finds Knowledge

```
CLAUDE.md (always loaded)
    │
    ├─ First-run check fails ────────→ reads tools/setup.md
    │                                   (Docker / HA / token / .env bootstrap)
    │
    ├─ "Before controlling a device" → reads tools/_common.md for ha-mcp patterns
    │                                   then device skill file for commands & quirks
    │                                   then tools/_services.md if unsure about a service
    │                                   then tools/_errors.md if a call fails
    │
    ├─ "Before creating automation" ─→ reads tools/automations/_guide.md
    │                                   then _reference.md for JSON schema
    │
    └─ "Before adding integration" ──→ reads tools/integrations/_guide.md

TOOLS.md (loaded on demand)
    └─ Quick Reference table maps device names → skill files

Destructive ha-mcp calls (create/modify/delete automations, scripts, integrations,
devices, backups, restarts, HACS downloads)
    └─ scripts/approval-gate.py runs as a Claude Code PreToolUse hook and blocks
       the call unless the user's latest message is an explicit "yes / confirm"
```

Skill files are loaded **on demand**, not all at once. The agent only reads what it needs for the current task — this keeps the LLM context small and replies fast.

---

## Requirements

- **OpenClaw CLI** — the AI agent framework
- **Docker** — runs Home Assistant
- **uv** — Python package manager for running ha-mcp
- **A messaging platform** — Discord, Telegram, WhatsApp, Feishu, or any platform supported by OpenClaw
- **Claude API access** — OpenClaw uses Claude as its backend

## Troubleshooting

**Bot doesn't respond:**
- Check the bot is online in your messaging app
- Verify your channel config in `openclaw.json` is correct — see the [OpenClaw Getting Started guide](https://docs.openclaw.ai/start/getting-started)
- Check logs: `openclaw gateway logs --profile smarthub`

**HA is unreachable:**
- Run `docker ps` — is `homeassistant` running?
- Test: `curl http://localhost:8123/api/config -H "Authorization: Bearer YOUR_TOKEN"` — should return config JSON with fields like `version`, `state`, and `config_source`
- Check `.env` has the correct token

**OAuth redirect fails (Xiaomi, Google, etc.):**

The OAuth login redirects to `homeassistant.local:8123` (or whichever port HA is running on — check `HA_URL` in `.env`). This works via mDNS if your computer is on the same network. If it doesn't resolve, add the Pi's IP to your hosts file — OpenClaw will detect the IP and give you the exact command.

*Windows* — run Command Prompt as administrator:

![Run CMD as administrator](docs/cmd-run-as-admin.png)

Then paste the command OpenClaw gave you:

![Paste the hosts command](docs/cmd-paste-command.png)

*Mac / Linux:*
```bash
echo "<PI_IP> homeassistant.local" | sudo tee -a /etc/hosts
```

**Tunnel not working:**
- Check `cloudflared` is running: `ps aux | grep cloudflared`
- Verify `trusted_proxies: 127.0.0.1` under `http:` in HA's `configuration.yaml`
