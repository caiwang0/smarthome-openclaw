# Phase 1 MVP — Issue Document

**Date:** 2026-03-26
**Scope:** Phase 1 MVP implementation — Unified Smart Device Dashboard wrapping Home Assistant
**Sources:** ha-research.md (HA architecture/API research), ha-research-prompt.md (project spec), onepager.md (product spec)

## Summary

Phase 1 MVP requires building a three-service Docker Compose stack (Home Assistant + Elysia/Bun API + React/nginx dashboard) that auto-discovers smart home devices, displays them with live status, and provides basic control (lights, switches, thermostats, cameras, sensors) organized by room. The system must work out-of-the-box with zero manual device configuration. Eleven discrete implementation gaps are identified below.

## Findings

### P1: Docker Compose Multi-Service Setup

**Severity:** Critical
**Category:** Infrastructure
**Affected components:** `docker-compose.yml`, service configs, networking

**Description:** No Docker Compose configuration exists. The system requires three services:
1. **Home Assistant** — `ghcr.io/home-assistant/home-assistant:stable` with `network_mode: host` (mandatory for mDNS/SSDP/DHCP device discovery), `privileged: true` (USB access), `/run/dbus` mount (Bluetooth), timezone config (`Asia/Kuala_Lumpur`), and a persistent config volume.
2. **Elysia API** (Bun runtime) — WebSocket client to HA + REST proxy for the dashboard. Needs `HA_URL` and `HA_TOKEN` env vars.
3. **React Dashboard** (nginx) — Static build served via nginx, proxied to API service.

Since HA uses host networking, the API and dashboard services must also use host networking or be configured to reach HA on the host's port 8123.

**Impact:** Without this, nothing runs. Host networking is non-negotiable — bridge mode blocks device discovery broadcasts.

**Success criteria:**
- [ ] `docker compose up` starts all three services without errors
- [ ] HA accessible at `http://localhost:8123`
- [ ] API accessible at `http://localhost:3001`
- [ ] Dashboard accessible at `http://localhost:3000`
- [ ] HA discovers devices on the local network (mDNS/SSDP works)

---

### P2: HA WebSocket Client with Authentication

**Severity:** Critical
**Category:** Backend / Integration
**Affected components:** API service — HA connection module

**Description:** The API service needs a persistent WebSocket connection to Home Assistant using the `home-assistant-js-websocket` npm package. Auth flow:
1. Connect to `ws://{HA_URL}/api/websocket`
2. Server sends `{"type": "auth_required"}`
3. Client sends `{"type": "auth", "access_token": "TOKEN"}`
4. Server sends `{"type": "auth_ok"}`

Must use `createLongLivedTokenAuth()` and `createConnection()` from the library. The connection must handle reconnection automatically (the library does this). Long-lived access tokens are created from HA UI → Profile → Security tab — HA does NOT save the token after creation.

**Impact:** Without a working WebSocket connection, no data flows from HA to our system. Everything else depends on this.

**Success criteria:**
- [ ] API service connects to HA WebSocket on startup
- [ ] Authentication succeeds with a long-lived access token
- [ ] Connection auto-reconnects after disconnection
- [ ] Connection state is logged (connected/disconnected/reconnecting)

---

### P3: Device Aggregation Service

**Severity:** Critical
**Category:** Backend / Data
**Affected components:** API service — device aggregation module

**Description:** A complete device list requires combining THREE separate HA registries plus entity states:

1. **Device Registry** (`config/device_registry/list`) — physical device metadata: `id`, `identifiers`, `connections` (MAC addresses), `manufacturer`, `model`, `name`, `area_id`, `via_device`, `sw_version`, `hw_version`
2. **Entity Registry** (`config/entity_registry/list`) — maps entities to devices: `entity_id`, `device_id`, `area_id` (can override device's area), `platform`
3. **Area Registry** (`config/area_registry/list`) — rooms: `area_id`, `name`
4. **Entity States** (`get_states`) — current state + attributes for every entity

The hierarchy: Area → Device → Entity (with state). Entity `area_id` overrides device `area_id`.

Key state values: `"unavailable"` = device offline, `"unknown"` = no data yet. All state values are strings.

Must produce a unified device list combining: device metadata (name, manufacturer, model), network info (MAC/IP from `connections`), entities with current states, online/offline status, and area assignment.

**Impact:** Without aggregation, the dashboard has no data to display. This is the core data pipeline.

**Success criteria:**
- [ ] Fetches all 3 registries + entity states from HA via WebSocket
- [ ] Produces a unified device list with: device name, manufacturer, model, MAC, area, entities with states
- [ ] Correctly determines online/offline status: device is offline when ALL its entities are `"unavailable"` (a single unavailable entity on a multi-entity device does not mean the device is offline)
- [ ] Handles entity area override (entity `area_id` takes precedence over device `area_id`)
- [ ] Exposes aggregated data via REST endpoint (`GET /api/devices`)

---

### P4: Real-Time State Updates via Event Subscription

**Severity:** High
**Category:** Backend / Real-time
**Affected components:** API service — event subscription module

**Description:** After initial load, the system must receive real-time state updates. Two approaches:
- `subscribeEntities()` from `home-assistant-js-websocket` — auto-diffs, sends only changes (recommended)
- `subscribe_events` with `event_type: "state_changed"` — raw event stream

`state_changed` events contain `old_state` and `new_state` objects. The `last_changed` timestamp only updates when the `state` value changes; `last_updated` updates on any attribute change.

The API must update its internal device list on each state change. The dashboard polls for updates every 10 seconds (SSE/WebSocket push deferred to post-MVP).

**Impact:** Without real-time updates, the dashboard shows stale data. Users won't see devices go online/offline.

**Success criteria:**
- [ ] Subscribes to entity state changes on HA connection
- [ ] Internal device list updates within 1 second of HA state change
- [ ] Dashboard reflects state changes via polling every 10 seconds
- [ ] Online/offline transitions are detected and reflected

---

### P5: REST API Endpoints for Dashboard

**Severity:** High
**Category:** Backend / API Design
**Affected components:** API service — Elysia routes

**Description:** The Elysia API must expose REST endpoints for the React dashboard:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `GET /api/devices` | GET | Aggregated device list with states |
| `GET /api/devices/:id` | GET | Single device detail |
| `GET /api/areas` | GET | Area/room list |
| `POST /api/services/:domain/:service` | POST | Proxy service calls to HA |
| `GET /api/camera/:entity_id/snapshot` | GET | Proxy camera snapshot from HA |

Service call endpoint must accept `entity_id` (or array), `area_id`, and `service_data` in the request body, then forward to HA via `callService()` or REST `POST /api/services/{domain}/{service}`.

Camera snapshot proxies `GET /api/camera_proxy/{entity_id}` from HA, passing through the auth header.

**Impact:** Without API endpoints, the dashboard has no backend to talk to.

**Success criteria:**
- [ ] `GET /api/devices` returns aggregated device list as JSON
- [ ] `GET /api/areas` returns area list
- [ ] `POST /api/services/light/turn_on` with `{"entity_id": "light.x"}` toggles the light in HA
- [ ] `GET /api/camera/:entity_id/snapshot` returns a JPEG image
- [ ] Error responses include meaningful status codes and messages

---

### P6: React Dashboard — Device Card Grid

**Severity:** High
**Category:** Frontend / UI
**Affected components:** React app — components, pages, styles

**Description:** Card-based grid layout showing all discovered devices. Each card displays:
- Device name (friendly name)
- Manufacturer and model
- IP address and/or MAC address (from device registry `connections` field)
- Color-coded status badge: green = online, red = offline/unavailable, yellow = unknown
- Device type icon (light, switch, sensor, camera, climate, etc.)

Grid must be responsive. Cards grouped by room/area with section headers. "Unassigned" group for devices without an area.

Auto-refreshes every 10 seconds by re-fetching `GET /api/devices`.

**Impact:** This is the primary user interface. Without it, users have no way to see their devices.

**Success criteria:**
- [ ] Dashboard loads and displays device cards in a responsive grid
- [ ] Each card shows: name, manufacturer/model, IP/MAC, status badge
- [ ] Status badges are color-coded (green/red/yellow)
- [ ] Cards are grouped by room with section headers
- [ ] Unassigned devices appear in a separate group
- [ ] Data auto-refreshes every 10 seconds

---

### P7: Device Control — Lights, Switches, Thermostat

**Severity:** High
**Category:** Frontend + Backend / Control
**Affected components:** React components, API service call proxy

**Description:** Interactive controls on device cards:

| Device Type | Control | Service Call | Parameters |
|------------|---------|-------------|------------|
| Lights | On/off toggle + brightness slider | `light.turn_on` / `light.turn_off` | `brightness` (0-255), `rgb_color` |
| Switches/Plugs | On/off toggle | `switch.turn_on` / `switch.turn_off` / `switch.toggle` | — |
| Thermostat | Temperature +/- buttons, mode selector | `climate.set_temperature` / `climate.set_hvac_mode` | `temperature`, `hvac_mode` (heat/cool/auto/off) |

Service calls go through our API (`POST /api/services/:domain/:service`) which proxies to HA.

Thermostat cards should show: current temperature (from state), target temperature (from `target_temperature` attribute), available HVAC modes (from `hvac_modes` attribute), and min/max temp constraints.

Light cards should show current brightness level and on/off state.

**Impact:** Without controls, the dashboard is view-only. Users expect to interact with their devices.

**Success criteria:**
- [ ] Light cards have on/off toggle that calls `light.turn_on`/`light.turn_off`
- [ ] Light cards have brightness slider that calls `light.turn_on` with `brightness` parameter
- [ ] Switch cards have on/off toggle that calls `switch.toggle`
- [ ] Thermostat cards show current temp, target temp, and HVAC mode
- [ ] Thermostat cards allow setting temperature and changing mode
- [ ] Controls provide visual feedback (optimistic update + confirmation from HA state change)

---

### P8: Camera Feed Display

**Severity:** Medium
**Category:** Frontend / Media
**Affected components:** React camera component, API proxy endpoint

**Description:** Camera entities should display a snapshot image on the card, with option to view a live feed.

Three approaches (from research):
- **Snapshot** — `GET /api/camera_proxy/{entity_id}?time={timestamp}` returns JPEG. Simplest. Periodic refresh.
- **MJPEG** — works in an `<img>` tag with `src` pointing to stream URL. Simple but bandwidth-heavy.
- **HLS** — requires `hls.js` player and the `stream` integration enabled in HA.

For MVP: use snapshot with periodic refresh (every 10 seconds). Camera card shows the latest snapshot image. Click/tap to open larger view.

**Impact:** Cameras are a key device type. Users expect to see their feeds.

**Success criteria:**
- [ ] Camera cards display a snapshot image
- [ ] Snapshot refreshes periodically (every 10 seconds)
- [ ] Clicking a camera card opens a larger view
- [ ] API proxies the camera snapshot from HA with proper auth

---

### P9: Room/Area Grouping and Navigation

**Severity:** Medium
**Category:** Frontend / UX
**Affected components:** React app — area filtering, layout

**Description:** Devices must be organized by room/area. The Area Registry provides `area_id` and `name` for each area. Devices link to areas via `area_id`. Entity `area_id` overrides device `area_id`.

UI should provide:
- "All Devices" view (default) — all devices grouped by area with section headers
- Area filter/tabs — click an area to show only devices in that area
- "Unassigned" group for devices without an `area_id`
- Device count per area

**Impact:** Without room grouping, large device lists are unnavigable. This is a core organizational feature.

**Success criteria:**
- [ ] Dashboard groups devices by area with section headers
- [ ] Area tabs/filters allow viewing a single area's devices
- [ ] "Unassigned" group shows devices with no area
- [ ] Each area shows a device count
- [ ] Area assignment respects entity override (entity `area_id` > device `area_id`)

---

### P10: Sensor Readings Display

**Severity:** High
**Category:** Frontend / UI
**Affected components:** React sensor card component, API device aggregation

**Description:** Sensor entities (`sensor.*`, `binary_sensor.*`) display read-only data — temperature, humidity, motion, power usage, etc. Each sensor entity has:
- `state` — the current reading as a string (e.g., `"23.5"`, `"on"`)
- `attributes.unit_of_measurement` — e.g., `"°C"`, `"%"`, `"W"`
- `attributes.device_class` — e.g., `"temperature"`, `"humidity"`, `"motion"`, `"power"`

Sensor cards should display the current value with its unit, an icon based on `device_class`, and the sensor name. Binary sensors (motion, door/window) show `"on"`/`"off"` state with appropriate labels (e.g., "Motion detected" / "Clear").

Note: All state values are strings — the frontend must parse numeric values for display formatting (e.g., `parseFloat("23.5")` for rounding).

**Impact:** Sensors are one of the most common device types. Users expect to see temperature, humidity, and motion data.

**Success criteria:**
- [ ] Sensor entities are identified by `entity_id` prefix `sensor.*` and `binary_sensor.*`
- [ ] Sensor cards display current value with `unit_of_measurement`
- [ ] Sensor cards show an icon based on `device_class` (temperature, humidity, motion, power)
- [ ] Binary sensor cards show human-readable labels ("Motion detected" / "Clear", "Open" / "Closed")
- [ ] Sensor cards are read-only (no controls)
- [ ] Sensor values update with the 10-second polling refresh

---

### P11: New Device Notifications

**Severity:** Medium
**Category:** Backend + Frontend / Notifications
**Affected components:** API service — device registry polling, React notification component

**Description:** When a new device joins the network and is discovered by HA, the dashboard should notify the user. Implementation approach for MVP:
- API service polls the device registry periodically (every 30 seconds) or subscribes to `device_registry_updated` events
- Compares current device list against previously known devices
- When a new device appears, flags it in the API response
- Dashboard shows a notification banner/toast: "New device discovered: [device name]"

New devices should be visually highlighted in the device grid (e.g., a "NEW" badge) for a configurable period.

**Impact:** Without notifications, users won't know when new devices are discovered — they'd have to manually check the list.

**Success criteria:**
- [ ] API detects when a new device appears in the HA device registry
- [ ] New device detection occurs within 30 seconds of HA discovering the device
- [ ] Dashboard displays a notification when a new device is discovered
- [ ] Newly discovered devices are visually highlighted in the grid
- [ ] Notification includes the device name

---

## Accepted Residual Risks

1. **Long-lived token management** — For MVP, the HA access token is stored as an environment variable in Docker Compose. Not rotated automatically. Acceptable for local-only deployment.
2. **No HTTPS** — All services communicate over HTTP on localhost. Acceptable for local network; will need TLS for remote access in future phases.
3. **Polling-based refresh** — Dashboard polls every 10 seconds instead of WebSocket push. Acceptable latency for MVP; SSE/WebSocket push can be added later.
4. **Snapshot-only cameras** — No live streaming in MVP. Periodic snapshot refresh is sufficient for Phase 1.
5. **HA onboarding required** — Home Assistant requires completing its first-time onboarding wizard (create user account, set location/timezone) before device discovery works. This is a one-time manual step that contradicts the "no setup" goal but cannot be automated. The onboarding must be completed at `http://localhost:8123` before the dashboard will show any devices. Future improvement: pre-seed HA config to skip onboarding.

## Dependencies Between Findings

```
P1 (Docker Compose) ← everything depends on this
  └── P2 (WebSocket Client) ← data pipeline foundation
        └── P3 (Device Aggregation) ← core data model
              ├── P4 (Real-time Updates) ← keeps data fresh
              ├── P11 (New Device Notifications) ← detects new devices
              └── P5 (REST API) ← serves data to frontend
                    ├── P6 (Device Cards) ← displays data
                    │     ├── P7 (Device Control) ← interacts with data
                    │     ├── P8 (Camera Feeds) ← specialized display
                    │     ├── P9 (Room Grouping) ← organizes display
                    │     └── P10 (Sensor Readings) ← read-only data display
```

P1 → P2 → P3 → P5 → P6 is the critical path. P4, P7, P8, P9, P10, P11 can be parallelized after their dependencies are met.
