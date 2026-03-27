# Home Assistant Wrapper — Design Spec

## Overview

A lightweight home device discovery and management dashboard that wraps Home Assistant as its backend engine. Users can discover Wi-Fi/IP devices on their home network and view them in a custom dashboard.

## Architecture

```
┌──────────────────────────────┐
│   React + TypeScript (UI)    │  Custom dashboard — device list, status, details
│   Port 3000                  │
├──────────────────────────────┤
│   Bun + Elysia (API Layer)   │  Proxies HA API, hides auth tokens, custom logic
│   Port 3001                  │
├──────────────────────────────┤
│   Home Assistant (Docker)    │  Device discovery (mDNS, SSDP, DHCP), control, automation
│   Port 8123                  │
└──────────────────────────────┘
     All containerized via Docker Compose
     Deployed on Raspberry Pi (portable via Docker)
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Discovery Engine | Home Assistant (Docker, `ghcr.io/home-assistant/home-assistant:stable`) |
| API Layer | Bun + Elysia (TypeScript) |
| Frontend | React + TypeScript + RSBuild |
| Deployment | Docker Compose on Raspberry Pi |
| Real-time | WebSocket (HA → API Layer → Frontend) |

## Phase Roadmap

### Phase 1: Discover & List (MVP) ← **Current Target**

**Goal:** Scan the home network and display all discovered devices in a dashboard.

**Capabilities:**
- Home Assistant runs in Docker with `network_mode: host` for LAN discovery
- Auto-discovers Wi-Fi/IP devices via mDNS (Chromecast, ESPHome, Apple TV), SSDP/UPnP (Sonos, smart TVs, routers), and DHCP (new devices joining network)
- Elysia backend connects to HA via WebSocket API, fetches device registry and entity states
- React dashboard shows device list with: name, manufacturer, model, IP/MAC, online/offline status, last seen
- Real-time updates when new devices appear or status changes

**HA API Usage (Phase 1):**
- WebSocket `config/device_registry/list` — get all physical devices (WebSocket-only, no REST endpoint)
- WebSocket `config/entity_registry/list` — map entities to devices (WebSocket-only, no REST endpoint)
- REST `GET /api/states` — current state of all entities
- WebSocket `subscribe_events: state_changed` — real-time status updates
- WebSocket `config_entries/flow/progress` — pending discovered (not yet configured) devices

**Data Model (API Layer):**
```typescript
interface Device {
  id: string;                    // HA device ID
  name: string;                  // Device name (user-set or default)
  manufacturer: string | null;
  model: string | null;
  ipAddress: string | null;      // Extracted from connections/attributes
  macAddress: string | null;     // From connections
  status: "online" | "offline" | "unknown";
  discoverySource: string;       // "zeroconf", "ssdp", "dhcp", etc.
  entityCount: number;           // Number of entities belonging to this device
  lastSeen: string;              // ISO 8601 timestamp
  area: string | null;           // Room/area assignment
}
```

**Online/Offline Logic:**
HA doesn't have a universal online/offline field. We infer it:
1. If all entities of a device have state `unavailable` → offline
2. If device has a `connectivity` binary sensor → use that
3. Otherwise → online

### Phase 2: Connect & Control (Future)

**Goal:** Add device control capabilities to the dashboard.

**Planned capabilities:**
- Toggle switches, lights on/off
- View camera streams (RTSP/MJPEG)
- Adjust thermostat temperature
- View sensor readings (temperature, humidity, motion)
- Group devices by room/area
- Service calls via HA REST API (`POST /api/services/<domain>/<service>`)

**New HA API usage:**
- `POST /api/services/light/turn_on` — control lights
- `POST /api/services/switch/toggle` — toggle switches
- `POST /api/services/climate/set_temperature` — thermostat control
- Camera proxy endpoint for streams

### Phase 3: Full Automation (Future)

**Goal:** Rule-based automation engine with scheduling and triggers.

**Planned capabilities:**
- Create automation rules (if X then Y)
- Time-based schedules (turn off lights at 10pm)
- Device-triggered actions (if motion detected, turn on lights)
- Scene management (presets for groups of devices)
- Notification system (alert when device goes offline)

**Approach:** Leverage HA's built-in automation engine via its API rather than building a custom one. The API layer translates user-friendly rules into HA automation YAML configs.

## Docker Compose Setup

```yaml
version: "3.9"
services:
  homeassistant:
    container_name: homeassistant
    image: ghcr.io/home-assistant/home-assistant:stable
    volumes:
      - ./ha-config:/config
      - /etc/localtime:/etc/localtime:ro
    environment:
      - TZ=Asia/Singapore
    restart: unless-stopped
    network_mode: host
    # Note: network_mode: host required for mDNS/SSDP device discovery
    # HA will be available on port 8123

  api:
    container_name: ha-wrapper-api
    build: ./api
    ports:
      - "3001:3001"
    environment:
      - HA_URL=http://localhost:8123
      - HA_TOKEN=${HA_TOKEN}
      - PORT=3001
    depends_on:
      - homeassistant
    network_mode: host
    restart: unless-stopped

  web:
    container_name: ha-wrapper-web
    build: ./web
    environment:
      - API_URL=http://localhost:3001
    depends_on:
      - api
    network_mode: host
    restart: unless-stopped
```

## Environment Variables

| Variable | Description | Example |
|----------|------------|---------|
| `HA_URL` | Home Assistant base URL | `http://localhost:8123` |
| `HA_TOKEN` | HA long-lived access token | `eyJhbG...` (created in HA UI) |
| `PORT` | API layer port | `3001` |
| `TZ` | Timezone | `Asia/Singapore` |

## Project Structure (Phase 1)

```
home-assistant/
├── docker-compose.yml
├── .env                        # HA_TOKEN (gitignored)
├── .gitignore
├── ha-config/                  # HA config volume (gitignored)
├── api/                        # Bun + Elysia backend
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   ├── src/
│   │   ├── index.ts            # Elysia server entry point
│   │   ├── ha-client.ts        # WebSocket + REST client for HA
│   │   ├── device-service.ts   # Device aggregation logic (registry + states → Device[])
│   │   ├── routes/
│   │   │   └── devices.ts      # GET /api/devices, GET /api/devices/:id
│   │   └── types.ts            # Shared TypeScript types
│   └── tests/
│       ├── device-service.test.ts
│       └── ha-client.test.ts
├── web/                        # React frontend
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   ├── rsbuild.config.ts
│   └── src/
│       ├── App.tsx
│       ├── main.tsx
│       ├── components/
│       │   ├── DeviceList.tsx       # Main device list view
│       │   ├── DeviceCard.tsx       # Individual device card
│       │   └── StatusBadge.tsx      # Online/offline indicator
│       ├── hooks/
│       │   └── useDevices.ts        # Fetch + WebSocket subscription
│       ├── types/
│       │   └── device.ts            # Device interface
│       └── styles/
│           └── global.css
└── docs/
    └── superpowers/
        ├── specs/
        │   └── 2026-03-24-home-assistant-wrapper-design.md
        └── plans/
            └── 2026-03-24-home-assistant-phase1.md
```

## Extensibility for Zigbee/Z-Wave

When ready to add Zigbee/Z-Wave support:
1. Plug USB dongle into Pi
2. Add `devices: ["/dev/ttyUSB0:/dev/ttyUSB0"]` and `privileged: true` to HA Docker service
3. Configure ZHA or Zigbee2MQTT integration in HA
4. No code changes needed — new devices appear in the same device registry API

## First-Time Setup Flow

1. `docker compose up` starts HA + API + Web
2. User visits `http://<pi-ip>:8123` to complete HA onboarding (create account)
3. User creates a long-lived access token in HA UI (Profile → Security → Long-Lived Access Tokens)
4. User sets `HA_TOKEN` in `.env` file
5. Restart API service — it connects to HA and starts syncing devices
6. User visits `http://<pi-ip>:3000` to see their device dashboard
