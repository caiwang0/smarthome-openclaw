# SmartHub — AI-Powered Smart Home

Control your Home Assistant with natural language through Discord, Teams, or Feishu. Powered by OpenClaw.

## How It Works

```
You (Discord/Teams/Feishu)
  │
  ▼
OpenClaw (AI agent)
  │
  ▼
SmartHub API (Bun/Elysia)
  │
  ▼
Home Assistant (Docker)
  │
  ▼
Your devices (lights, AC, TV, cameras, sensors, ...)
```

OpenClaw understands natural language — say "I'm leaving for work" and it turns off lights, locks doors, sets the AC to eco, and confirms what it did.

## Quick Install (Already have OpenClaw?)

If you already have OpenClaw running, just tell your bot:

> Run this: `curl -fsSL https://raw.githubusercontent.com/caiwang0/smarthome-openclaw/main/install.sh | bash`

Then tell it: **"Help me set up SmartHub"**

---

## Full Setup (Starting from scratch)

There are **3 manual steps**, then OpenClaw guides you through the rest.

### Step 1: Install OpenClaw

```bash
# macOS / Linux
curl -fsSL https://get.openclaw.dev | sh

# Or with npm
npm install -g @openclaw/cli
```

Verify it's installed:

```bash
openclaw --version
```

### Step 2: Create a Bot on Your Messaging Platform

You need a bot token so OpenClaw can send/receive messages.

**Discord:**
1. Go to https://discord.com/developers/applications
2. Click "New Application" — name it whatever you want (e.g., "SmartHub")
3. Go to **Bot** tab → click "Reset Token" → copy the token
4. Enable these under **Privileged Gateway Intents**: Message Content Intent
5. Go to **OAuth2** → URL Generator → select `bot` scope → select permissions: Send Messages, Read Message History, Add Reactions
6. Copy the generated URL, open it in your browser, and invite the bot to your server
7. Note down your **Guild ID** (server) and **Channel ID** — enable Developer Mode in Discord settings, then right-click server → Copy Server ID, right-click channel → Copy Channel ID

**Teams:** See [OpenClaw Teams Setup Guide](https://docs.openclaw.dev/channels/teams)

**Feishu:** See [OpenClaw Feishu Setup Guide](https://docs.openclaw.dev/channels/feishu)

### Step 3: Configure and Start OpenClaw

Once OpenClaw is running, it will ask you for the repo URL. You can use this one:

```
https://github.com/caiwang0/smarthome-openclaw
```

Or if you've forked it, send OpenClaw your fork URL and it will clone it for you.

Create the OpenClaw gateway config:

```bash
mkdir -p ~/.openclaw-smarthub
```

Create `~/.openclaw-smarthub/openclaw.json`:

```json
{
  "agents": {
    "defaults": {
      "model": {
        "primary": "anthropic/claude-sonnet-4-6"
      },
      "workspace": "/path/to/home-assistant",
      "timeoutSeconds": 600,
      "sandbox": {
        "mode": "off"
      }
    }
  },
  "tools": {
    "profile": "coding",
    "exec": {
      "security": "full",
      "ask": "off"
    }
  },
  "channels": {
    "discord": {
      "enabled": true,
      "token": "YOUR_DISCORD_BOT_TOKEN",
      "groupPolicy": "open",
      "allowFrom": [
        "YOUR_DISCORD_USER_ID"
      ],
      "guilds": {
        "YOUR_GUILD_ID": {
          "requireMention": false,
          "channels": {
            "YOUR_CHANNEL_ID": {
              "allow": true
            }
          }
        }
      }
    }
  },
  "gateway": {
    "port": 18790,
    "mode": "local",
    "bind": "loopback"
  },
  "plugins": {
    "entries": {
      "acpx": {
        "enabled": true,
        "config": {
          "cwd": "/path/to/home-assistant",
          "permissionMode": "approve-all",
          "nonInteractivePermissions": "deny",
          "timeoutSeconds": 600
        }
      }
    }
  }
}
```

Replace the placeholders:
- `YOUR_DISCORD_BOT_TOKEN` — from Step 2
- `YOUR_DISCORD_USER_ID` — right-click your name in Discord → Copy User ID
- `YOUR_GUILD_ID` — your server ID
- `YOUR_CHANNEL_ID` — the channel you want the bot in
- `/path/to/home-assistant` — absolute path to this cloned repo (both `workspace` and `cwd`)

Start the gateway:

```bash
openclaw gateway start --profile smarthub
```

Verify the bot comes online in your Discord channel. Send it a message — if it responds, you're good.

---

## From Here, OpenClaw Guides You

Once OpenClaw is running in your messaging channel, tell it:

> **"Help me set up SmartHub"**

OpenClaw will walk you through everything else:

### What OpenClaw handles for you:

| Step | What happens |
|------|-------------|
| **Install Docker** | Checks if Docker is installed, gives you the install command if not |
| **Start Home Assistant** | Runs `docker compose up -d` to launch HA and the API |
| **HA First-Time Setup** | Tells you to open `http://localhost:8123` in your browser, create your admin user, and walks you through each screen |
| **Get Access Token** | Guides you: Profile → Security → Long-Lived Access Tokens → Create Token → copy it back to the chat |
| **Configure .env** | Takes the token you pasted and writes it to `.env` |
| **Restart API** | Restarts the API container so it picks up the new token |
| **Verify Connection** | Confirms HA is reachable and lists any devices already connected |
| **Set Up Tunnel** | Installs `cloudflared` and creates a public URL for remote access |
| **Add Integrations** | Walks you through adding Xiaomi, Philips Hue, Broadlink, or any other brand |
| **Discover Devices** | Shows you what devices were found after each integration |

---

### Example conversation:

```
You:      Help me set up SmartHub
OpenClaw: Let's get your smart home running. First, send me your SmartHub repo URL
          (or I can use the default: https://github.com/caiwang0/smarthome-openclaw)

You:      Just use the default
OpenClaw: Got it. Do you have Docker installed? Run: docker --version

You:      Docker version 27.5.1
OpenClaw: Docker is ready. Let me clone the repo and start Home Assistant...
          Running: git clone https://github.com/caiwang0/smarthome-openclaw && cd smarthome-openclaw && docker compose up -d
          ...
          HA is starting up. Open http://localhost:8123 in your browser.
          You'll see the onboarding wizard — create your admin account
          (pick a username and password). Let me know when you're done.

You:      Done, I created user "alice"
OpenClaw: Great. Now go to your profile (click your initial in the bottom-left),
          then Security tab → Long-Lived Access Tokens → Create Token.
          Name it "openclaw" and paste the token here.

You:      eyJhbGciOiJIUzI1NiIs...
OpenClaw: Got it. I've saved the token to .env and restarted the API.
          Let me verify the connection...
          Connected to Home Assistant 2026.3.4 — 0 devices found.
          Want to set up remote access with a public URL, or add your
          first device integration?
```

## What You Can Do After Setup

Once everything is connected, talk to OpenClaw naturally:

| Say this | OpenClaw does this |
|----------|-------------------|
| "Turn off the living room lights" | Controls the device via HA |
| "I'm leaving for work" | Turns off lights, sets AC to eco, locks doors |
| "Why is the bedroom so hot?" | Checks sensors, AC state, and diagnoses the issue |
| "What devices do I have?" | Lists all connected devices by room |
| "Add a new integration" | Walks you through the setup flow |
| "Set the AC to 24" | Calls the climate service |

## Architecture

```
home-assistant/
├── ha-config/           # Home Assistant configuration (mounted into Docker)
├── api/                 # SmartHub API — Bun/Elysia, proxies to HA
│   └── src/
│       ├── index.ts         # API entry point
│       ├── ha-client.ts     # WebSocket connection to HA
│       └── routes/          # API routes (devices, areas, services, chat, camera)
├── tools/               # OpenClaw skill files — device knowledge, commands, quirks
│   ├── _common.md           # Shared API patterns and auth
│   ├── automations/         # Automation creation guide
│   ├── xiaomi-home/         # Xiaomi-specific commands and quirks
│   └── printer/             # Printer commands
├── docker-compose.yml   # Runs HA + API
├── .env                 # HA token, API port, timezone
├── CLAUDE.md            # OpenClaw's system instructions for this project
├── TOOLS.md             # Skill router — maps devices to skill files
└── docs/                # Research, specs, design docs
```

## Requirements

- **OpenClaw CLI** — the AI agent
- **Docker** — runs Home Assistant
- **A messaging platform** — Discord, Teams, or Feishu (for talking to OpenClaw)
- **Claude API access** — OpenClaw uses Claude as its AI backend

## Troubleshooting

**Bot doesn't respond in Discord:**
- Check that the bot is online (green dot) in the member list
- Make sure `requireMention` is `false` in `openclaw.json` if you don't want to @mention it
- Check `allowFrom` includes your Discord user ID
- Check the gateway logs: `openclaw gateway logs --profile smarthub`

**HA is unreachable:**
- Run `docker ps` — is the `homeassistant` container running?
- Try `curl http://localhost:8123/api/ -H "Authorization: Bearer YOUR_TOKEN"` — should return `{"message": "API running."}`
- Check `.env` has the correct token

**OAuth redirect fails during integration setup (Xiaomi, Google Home, etc.):**

The OAuth login redirects your browser to `homeassistant.local:8123`. This usually works automatically via mDNS if your computer is on the same network as the Pi. If it doesn't, you need to add the Pi's IP to your hosts file. OpenClaw will detect the IP and give you the exact command.

*Windows* — search `cmd` in Start menu, right-click Command Prompt, click **Run as administrator**:

![Run CMD as administrator](docs/cmd-run-as-admin.png)

Then paste the command OpenClaw gave you:

![Paste the hosts command](docs/cmd-paste-command.png)

*Mac / Linux:*
```bash
echo "<PI_IP> homeassistant.local" | sudo tee -a /etc/hosts
```

**Tunnel not working:**
- Make sure `cloudflared` is running: `ps aux | grep cloudflared`
- Check HA's `configuration.yaml` has `trusted_proxies: 127.0.0.1` under `http:`
