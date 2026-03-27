# Home Assistant Research & Phase 1 MVP Implementation Prompt

I'm building an AI-powered smart home hub that wraps Home Assistant as the backend engine. Before we start implementing, I need you to deeply understand how Home Assistant works so we can build on top of it correctly.

## Step 1: Research HA using context7

Use the context7 MCP tool to look up the Home Assistant Core documentation and codebase (library: `home-assistant/core`). Research and explain the following areas:

### Architecture & Core Concepts
- How HA's core architecture works — the event bus, state machine, service registry, and how they connect
- How integrations/components are structured (the `homeassistant/components/` pattern)
- How HA runs in Docker and what networking requirements it has (host networking for device discovery)

### Device Discovery & Registry
- How auto-discovery works — what protocols HA uses (mDNS/Zeroconf, SSDP/UPnP, HomeKit, DHCP)
- How the device registry works (`device_registry`) — what data it stores (name, manufacturer, model, identifiers)
- How the entity registry works (`entity_registry`) — relationship between devices and entities
- How entity states work — what a state object looks like, how states update in real-time

### APIs We Need to Use
- The WebSocket API — authentication flow, subscribing to state changes, fetching device/entity registries
- The REST API — fetching states, calling services, creating automations
- Long-lived access tokens — how to generate and use them
- Specific WebSocket commands we'll need: `config/device_registry/list`, `config/entity_registry/list`, `get_states`, `subscribe_events`

### Device Control
- How services work — the pattern for calling `light.turn_on`, `switch.toggle`, `climate.set_temperature`, etc.
- How to send commands to devices through HA's service layer

### IR Blaster Integration (research only — Phase 3)
- How the Broadlink integration works (`homeassistant/components/broadlink/`)
- How IR learning and sending works through HA
- How to send IR commands via the API (`remote.send_command` service)

### Automations (research only — Phase 2)
- How HA automations are structured (triggers, conditions, actions)
- How to create/modify/delete automations via the API (not YAML, through WebSocket/REST)
- The automation data model — what JSON structure HA expects

### For each area, provide:
- How it works internally
- The specific API calls or WebSocket commands we need
- Code examples or JSON payloads where relevant
- Any gotchas, limitations, or things that are poorly documented

## Step 2: Map to our system

After researching, create a mapping document:

| Our Feature (from onepager) | HA Concept | API/Method | Notes |
|-|-|-|-|
| Auto-discover devices | ? | ? | ? |
| Show device list with status | ? | ? | ? |
| Real-time online/offline | ? | ? | ? |
| Toggle lights/switches | ? | ? | ? |
| View camera feeds | ? | ? | ? |
| Adjust thermostat | ? | ? | ? |
| Room/area grouping | ? | ? | ? |
| View sensor readings | ? | ? | ? |
| Control AC via IR blaster (Phase 3) | ? | ? | ? |
| Create automations from AI (Phase 2) | ? | ? | ? |

Fill in every row based on what you learned.

## Step 3: Implementation — Phase 1 MVP Only

Once the research is complete and I've reviewed it, run `/review-driven-workflow` to plan and execute **Phase 1 only (the MVP)**.

### Phase 1 Scope (Weeks 1-6): Unified Smart Device Dashboard

- Docker Compose setup: Home Assistant (host networking) + Elysia API (Bun) + React dashboard (nginx)
- HA WebSocket client: persistent connection, authenticate with long-lived access token, fetch device/entity registries
- Device aggregation service: combine device registry + entity registry + entity states into a clean device list with online/offline status
- React dashboard: card-based grid showing all devices with name, manufacturer/model, IP, MAC, and color-coded status badge, auto-refresh every 10 seconds
- Device control: toggle lights/switches on/off, adjust thermostat, view camera feeds, view sensor readings from the dashboard
- Room/area grouping: organize devices by room

### Phase 1 is NOT:
- AI chat or automations (Phase 2)
- IR blaster remote learning and control (Phase 3)

The goal is: **open browser → every smart device in the home is already there with live status and control. No setup, no pairing, no YAML.**

## Reference docs to read first:
- `/home/edgenesis/Downloads/home-assistant/docs/onepager.md` — our product spec
- `/home/edgenesis/Downloads/home-assistant/docs/appendix.md` — strategy, phases, revenue model

## Important:
Do NOT start implementing anything until the research (Steps 1 & 2) is reviewed and approved. Research first, build second.
