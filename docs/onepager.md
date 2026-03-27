# Who

This guide is for anyone setting up a smart home device dashboard — homeowners, tinkerers, or developers who want to automatically discover and manage all devices on their home network from a single interface, without manually configuring each one.

# What

An AI-powered smart home system — all in one web app. It auto-discovers every device on your home network and gives you two ways to manage them:

1. **Dashboard** — see all devices, tap to control, build automations visually
2. **AI Chat (OpenClaw)** — type what you want in plain English, the AI does it

**Final product:** A web app running on a Raspberry Pi that acts as your home's command center. Describe what you want — "turn off everything when I leave" — and the AI creates the automation for you. Users can also create and manage OpenClaw skills directly in the web app to extend what the AI can do.

### Feature Checklist

| Feature | Phase | Status |
|---------|-------|--------|
| Auto-discover Wi-Fi/IP devices (smart plugs, cameras, TVs, speakers) | Phase 1 | MVP |
| Device dashboard with name, manufacturer, model, IP/MAC | Phase 1 | MVP |
| Real-time online/offline status monitoring | Phase 1 | MVP |
| New device notifications (device appears when it joins network) | Phase 1 | MVP |
| Toggle lights and switches on/off from dashboard | Phase 1 | MVP |
| View live camera feeds | Phase 1 | MVP |
| Adjust thermostat temperature | Phase 1 | MVP |
| Group devices by room/area | Phase 1 | MVP |
| View sensor readings (temperature, humidity, motion) | Phase 1 | MVP |
| OpenClaw AI chat in web app — control devices via natural language | Phase 2 | Planned |
| "Vibe" automations — describe rules in plain English, AI creates them | Phase 2 | Planned |
| AI notifications in chat (e.g., "AC turned on", "unknown device joined") | Phase 2 | Planned |
| Create and manage OpenClaw skills from the web app | Phase 2 | Planned |
| Visual automation rule builder on web app | Phase 2 | Planned |
| Time-based schedules (turn off lights at 10pm) | Phase 2 | Planned |
| Trigger-based actions (motion detected → record camera) | Phase 2 | Planned |
| Alerts when device goes offline or unknown device appears | Phase 2 | Planned |
| IR blaster control for normal devices (AC, fan, old TV) | Phase 3 | Planned |
| IR remote learning through the dashboard | Phase 3 | Planned |
| Zigbee/Z-Wave device support (with USB dongle hardware) | Phase 3 | Planned |

### What Devices Can We Connect To?

**Smart devices** (connect to Wi-Fi) — detected and controlled automatically:
- **Lights** — Philips Hue, IKEA TRADFRI, Shelly → on/off, dim, change color
- **Plugs** — TP-Link Kasa, Wemo, Shelly → on/off, power usage
- **Cameras** — Ring, Reolink, Hikvision → live feed, record clips
- **TVs** — Samsung, LG, Sony → on/off, volume, input
- **Speakers** — Sonos, Google Home, HomePod → play/pause, volume
- **Thermostats** — Nest, Ecobee → set temperature
- **Robot vacuums** — Roborock, Roomba → start/stop, schedule

**Normal devices** (no Wi-Fi) — controlled via a Wi-Fi IR blaster (~$20 per room, Phase 3):
- Place one IR blaster in each room → it learns your existing remotes and replays the signals on command
- Works with any device that has a remote — AC, TV, fan, projector, sound system, etc.
- Each device responds to different signals, so "turn on AC" won't affect the fan
- Example: Broadlink RM4 Mini — auto-discovered by Home Assistant, controlled from the dashboard
- In Phase 1, the IR blaster itself shows up as a discovered device; full remote learning and control comes in Phase 3

**How detection works:** Devices on your Wi-Fi announce themselves to the network. Home Assistant listens for these announcements and matches them against 2,000+ known device types to identify what they are and what they can do. No scanning, no manual setup.

### Technical Components

1. **Home Assistant** (https://github.com/home-assistant/core, ~86k GitHub stars) — the open-source engine that handles device discovery, communication, and control. We run it in Docker and use its API.
2. **API Layer (Bun + Elysia)** — our backend that talks to Home Assistant, combines device info into a clean list, and serves it to the dashboard.
3. **Dashboard (React)** — the web UI showing all your devices with live status updates.

# Why

### The Problem

70-80% of smart home households own a mix of smart devices and "dumb" devices (ACs, fans, old TVs) that their Alexa or Google Home can't control. 85-90% of installed AC units are still non-smart. The average home has 4 remote controls and users juggle 5-10 apps — 69% aren't even on a single platform. 1 in 3 Americans get frustrated with their smart home at least once a week.

The current options to fix this are bad:
- **Replace the device** — $800-2,000 for a smart AC
- **Buy an IR blaster** — $20-70, but Broadlink has a terrible app, SwitchBot requires cloud, and Sensibo/Tado only do ACs and charge subscriptions (Tado now charges $0.99/mo just to open the app)

### Our Solution

A $20 IR blaster per room + our hub makes every device smart — controlled from one dashboard and AI chat (WhatsApp/Telegram). No cloud, no subscription, no app juggling.

### Why It Will Work

1. **Massive underserved market.** The IR blaster hub market is $2.3B (2024) → $7.2B by 2033. 87% of global homes still have non-smart appliances. The retrofit pitch ($20/room vs $800+ replacement) sells itself.

2. **Competitors are poorly serving this space.** Broadlink is the cheapest ($26) but has the worst app in the category. SwitchBot ($70) requires cloud — your devices die if their servers go down. Sensibo ($119) and Tado ($179) only control ACs and paywall basic features behind subscriptions. No product combines all-device IR control + smart device unification + AI automation + local processing + no mandatory subscription.

3. **We leverage 10+ years of open-source work.** Home Assistant (86k GitHub stars, 2M+ users) already supports 2,000+ device integrations and auto-discovers IR blasters like Broadlink. We wrap it as an engine and add what it lacks: a simple UI, unified IR control, and AI chat. We skip the hardest part (device protocol support) entirely.

4. **Privacy is becoming a purchase driver.** 57% of Americans are concerned about smart home data collection. Every major competitor requires cloud. We run fully local — no data leaves the home, and the system works even when internet goes down.

5. **OpenClaw turns setup and automation from the hardest part into the easiest.** The #1 reason smart home products get returned (36% of all returns) is setup difficulty. 52% of DIY users hit setup issues, and 22% just give up. OpenClaw eliminates this — users describe what they want in plain English via WhatsApp or Telegram ("turn off AC when I leave", "dim lights at 10pm") and the AI builds the automation. No app to install, no rules to configure, no technical knowledge needed. This is the interaction model non-technical users already understand: texting. It also makes our product stickier — the more automations the AI creates, the more personalized and hard to leave the system becomes.

# How

## System Architecture

```
         Your Home Network (Wi-Fi / Ethernet)
         ┌──────────────────────────────────────────────────┐
         │                                                  │
   Smart devices            Normal devices                  │
   (auto-discovered)        (via IR blaster)                │
         │                        │                         │
  ┌──────┴──────┐          ┌──────┴──────┐                  │
  │ Smart TV    │          │ AC unit     │                  │
  │ Smart plug  │          │ Ceiling fan │                  │
  │ IP camera   │          │ Old TV      │                  │
  │ Speaker     │          │ Projector   │                  │
  │ Thermostat  │          │             │                  │
  └──────┬──────┘          └──────┬──────┘                  │
         │ Wi-Fi                  │ IR signals              │
         │                  ┌─────┴─────┐                   │
         │                  │ Wi-Fi IR  │                   │
         │                  │ Blaster   │ (one per room)    │
         │                  └─────┬─────┘                   │
         │                        │ Wi-Fi                   │
         └────────────┬───────────┘                         │
                      │                                     │
┌─────────────────────v─────────────────────────────────────┘
│
│  Raspberry Pi (Docker Compose)
│
│  ┌─────────────────────────────────────────────────────┐
│  │  Home Assistant (:8123)                             │
│  │                                                     │
│  │  Listens on the network for device announcements    │
│  │  Matches against 2,000+ known device integrations   │
│  │  Talks to IR blasters to control normal devices     │
│  │  Tracks device status in real-time                  │
│  └──────────────────────┬──────────────────────────────┘
│                         │
│  ┌──────────────────────v──────────────────────────────┐
│  │  API Layer (:3001)                                  │
│  │                                                     │
│  │  Fetches device list from Home Assistant             │
│  │  Determines online/offline status                    │
│  │  Sends control commands (Phase 1)                    │
│  │  Manages automation rules (Phase 2)                  │
│  └──────────────────────┬──────────────────────────────┘
│                         │
│  ┌──────────────────────v──────────────────────────────┐
│  │  Web App (:3000)                                    │
│  │                                                     │
│  │  ┌─────────────────┐  ┌──────────────────────────┐  │
│  │  │   Dashboard     │  │   OpenClaw AI Chat       │  │
│  │  │                 │  │                          │  │
│  │  │  Device list    │  │  "Turn on the AC"        │  │
│  │  │  Status badges  │  │  "Set lights to 50%"     │  │
│  │  │  Control buttons│  │  "Create a rule: turn    │  │
│  │  │  Room grouping  │  │   off everything at 11pm"│  │
│  │  │  Automation     │  │                          │  │
│  │  │  rule builder   │  │  AI notifications:       │  │
│  │  │                 │  │  "AC turned on ✓"        │  │
│  │  │                 │  │  "Unknown device joined"  │  │
│  │  └─────────────────┘  └──────────────────────────┘  │
│  │                                                     │
│  │  Skill builder — create/manage OpenClaw skills      │
│  └─────────────────────────────────────────────────────┘
│
│  User opens browser → http://raspberry-pi:3000
│
└─────────────────────────────────────────────────────────

```

## How It Works

```
Smart device connects to Wi-Fi
  → Home Assistant detects it automatically
    → Shows up in the dashboard with live status

Normal device (AC, fan, old TV)
  → Wi-Fi IR blaster in the room learns the remote codes (Phase 3)
    → Home Assistant sends IR commands through the blaster
      → Controlled from the dashboard just like a smart device

User chats with OpenClaw in the web app (Phase 2)
  → "Turn off everything when I leave the house"
    → AI creates the automation rule automatically
      → "Done — automation saved ✓"
```

## Phase 1: Unified Smart Device Dashboard (MVP — Weeks 1-6)

1. **Docker Compose Setup**: Three services — Home Assistant (host networking for discovery), Elysia API (WebSocket client + REST proxy), React dashboard (nginx serving static build). All on the same host network.
2. **HA WebSocket Client**: Persistent WebSocket connection to Home Assistant. Authenticates with long-lived access token. Fetches device and entity registries via WebSocket, entity states via REST.
3. **Device Aggregation Service**: Combines device registry, entity registry, and entity states into a clean device list with online/offline status.
4. **React Dashboard**: Card-based grid showing all devices with name, manufacturer/model, IP, MAC, and color-coded status badge. Auto-refreshes every 10 seconds.
5. **Device Control**: Toggle lights/switches on/off, adjust thermostats, view camera feeds, view sensor readings from the dashboard.
6. **Room/Area Grouping**: Organize devices by room.

## Phase 2: OpenClaw AI — Skills & Automations (Weeks 7-12)

7. **AI Chat in Web App**: Chat panel embedded in the dashboard. Ask OpenClaw to control devices, check status, or create automations in plain English.
8. **"Vibe" Automations**: Describe rules naturally — "when I leave, turn off everything" — and the AI generates them.
9. **Visual Automation Builder**: Create rules in the dashboard — if motion detected → turn on lights, at 10pm → turn off all lights.
10. **AI Notifications**: OpenClaw proactively messages you in the chat — "AC turned on", "unknown device joined your network".
11. **Alerts**: Notify when devices go offline or unknown devices join the network.
12. **Skill Builder**: Create, edit, and manage OpenClaw skills from the web app to extend what the AI can do.

## Phase 3: Make Dumb Devices Smart via IR (Weeks 13-18)

13. **IR Blaster Auto-Discovery**: Broadlink RM4 Mini (~$20) detected automatically by Home Assistant.
14. **IR Remote Learning**: Learn remote codes through the dashboard — point remote at blaster, press buttons, codes saved.
15. **IR Device Control**: AC, fan, old TV controllable from the same dashboard and AI chat.
16. **Zigbee/Z-Wave**: Add support via USB dongles — no code changes needed.
