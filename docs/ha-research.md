# Home Assistant Core Research

Research completed using context7 MCP against `home-assistant/core`, `home-assistant/developers.home-assistant`, `home-assistant/home-assistant-js-websocket`, and `home-assistant/home-assistant.io`.

---

## 1. Architecture & Core Concepts

### Event Bus
All communication in HA flows through a central **event bus**. When anything happens — a state changes, a service is called, a timer fires — an event is published. Components subscribe to events they care about. The most important event for us is `state_changed`, which fires every time an entity's state or attributes update.

### State Machine
Tracks every entity in the system. Each state object contains:
```json
{
  "entity_id": "light.bed_light",
  "state": "on",
  "attributes": {
    "brightness": 180,
    "rgb_color": [254, 208, 0],
    "friendly_name": "Bed Light",
    "supported_features": 147
  },
  "last_changed": "2016-11-26T01:37:24.265390+00:00",
  "last_updated": "2016-11-26T01:37:24.265390+00:00",
  "context": {
    "id": "326ef27d19415c60c492fe330945f954",
    "parent_id": null,
    "user_id": "31ddb597e03147118cf8d2f8fbea5553"
  }
}
```

**Key distinction:** `last_changed` only updates when the `state` value changes. `last_updated` updates on any attribute change too. States are always **strings** — even `"23.5"` for temperature.

### Service Registry
Services are callable actions exposed by integrations. Pattern: `{domain}.{service}` — e.g., `light.turn_on`, `switch.toggle`, `climate.set_temperature`. Each call takes optional `service_data` and `target` (which entities to act on).

### Integration/Component Structure
Located in `homeassistant/components/{domain}/`. Each has:
- `manifest.json` — declares name, dependencies, discovery protocols
- `__init__.py` — setup and teardown
- Config flow — handles auto-discovery and manual setup
- Platform files — `light.py`, `switch.py`, `sensor.py`, etc.

---

## 2. Device Discovery

HA listens on the network using **multiple protocols simultaneously**:

| Protocol | How It Works | Example |
|----------|-------------|---------|
| **mDNS/Zeroconf** | Listens for `_service._tcp.local.` broadcasts | Hue bridge, Shelly, ESPHome |
| **SSDP/UPnP** | Listens for UPnP device announcements | Samsung TVs, Sonos, routers |
| **DHCP** | Watches DHCP traffic for hostname/MAC patterns | Devices that don't announce themselves |
| **USB** | Detects USB vendor/product IDs | Zigbee/Z-Wave dongles |
| **MQTT** | Watches MQTT discovery topics | Zigbee2MQTT, Tasmota |

Each integration declares which protocols it supports in `manifest.json`:
```json
{
  "domain": "smart_device",
  "name": "Smart Device",
  "config_flow": true,
  "zeroconf": [{"type": "_smartdevice._tcp.local.", "name": "smartdevice-*"}],
  "ssdp": [{"st": "urn:schemas-upnp-org:device:SmartDevice:1"}],
  "dhcp": [{"hostname": "smartdevice-*", "macaddress": "00:1A:2B*"}]
}
```

**Gotcha:** `network_mode: host` in Docker is **mandatory** — bridge mode blocks mDNS/SSDP broadcasts and discovery won't work.

Extended discovery runs during onboarding and when visiting the integrations page.

---

## 3. Device Registry & Entity Registry

### Device Registry
Stores physical device metadata. WebSocket command: **`config/device_registry/list`**

Fields returned per device:
- `id` — internal UUID
- `identifiers` — set of `(domain, id)` tuples (unique per integration)
- `connections` — set of `(type, value)` e.g., `("mac", "AA:BB:CC:DD:EE:FF")`
- `manufacturer`, `model`, `model_id`, `name`
- `sw_version`, `hw_version`
- `area_id` — links to an area/room
- `config_entry_id` — which integration created it
- `via_device` — parent device (e.g., a Hue bridge)

### Entity Registry
Maps entities to devices. WebSocket command: **`config/entity_registry/list`**

- `entity_id` — e.g., `light.kitchen`
- `device_id` — links to device registry
- `area_id` — can **override** the device's area
- `platform` — which integration created it

### Area Registry
Rooms/zones. WebSocket command: **`config/area_registry/list`**

Returns areas with `area_id` and `name`. Devices link to areas via `area_id`.

### How They Connect
```
Area (area_id, name)
  └── Device (id, manufacturer, model, area_id)
        └── Entity (entity_id, device_id, state, attributes)
```

To build a complete device list, we must **combine all three** registries plus entity states.

---

## 4. APIs We Need

### WebSocket API — Authentication Flow

```
1. Connect to ws://localhost:8123/api/websocket
2. Server sends:  {"type": "auth_required", "ha_version": "2024.x.x"}
3. Client sends:  {"type": "auth", "access_token": "eyJ..."}
4. Server sends:  {"type": "auth_ok", "ha_version": "2024.x.x"}
5. Now send commands with incrementing "id" field
```

Raw JavaScript example:
```javascript
const ws = new WebSocket('ws://localhost:8123/api/websocket');

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);

  if (message.type === 'auth_required') {
    ws.send(JSON.stringify({
      type: 'auth',
      access_token: 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'
    }));
  } else if (message.type === 'auth_ok') {
    console.log('Authenticated successfully');
    // Now send commands
  }
};
```

### Key WebSocket Commands

| Command | Purpose | For Us |
|---------|---------|--------|
| `get_states` | Fetch all entity states | Initial load |
| `subscribe_events` (event_type: `state_changed`) | Real-time state updates | Live status |
| `config/device_registry/list` | All devices with metadata | Device list |
| `config/entity_registry/list` | All entities linked to devices | Entity → device mapping |
| `config/area_registry/list` | All rooms/areas | Room grouping |
| `call_service` | Control devices | Toggle lights, set temp |
| `stream_camera` | Get camera stream URLs | Camera feeds |

### REST API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/states` | GET | All entity states |
| `/api/states/{entity_id}` | GET | Single entity state |
| `/api/services/{domain}/{service}` | POST | Call a service |
| `/api/camera_proxy/{entity_id}` | GET | Camera snapshot image |
| `/api/camera_proxy_stream/{entity_id}` | GET | MJPEG stream |
| `/api/hls/.../playlist.m3u8` | GET | HLS live stream |

### Long-Lived Access Tokens
Created from **HA UI → Profile → Security tab → Long-Lived Access Tokens**. Or via WebSocket:
```json
{"type": "auth/long_lived_access_token", "client_name": "Our Hub", "lifespan": 365}
```
**Gotcha:** HA does NOT save the token — you must copy/store it immediately.

### JS WebSocket Library (`home-assistant-js-websocket`)

This npm package is purpose-built for what we need:
```javascript
import {
  createLongLivedTokenAuth,
  createConnection,
  subscribeEntities,
  callService
} from "home-assistant-js-websocket";

// Connect with long-lived token
const auth = createLongLivedTokenAuth("http://localhost:8123", "YOUR_TOKEN");
const connection = await createConnection({ auth });

// Real-time entity updates (auto-diffs, sends only changes)
subscribeEntities(connection, (entities) => {
  console.log(entities['light.kitchen'].state);       // "on"
  console.log(entities['sensor.temperature'].state);   // "23.5"
});

// Control a device
await callService(connection, 'light', 'turn_on',
  { brightness: 255, rgb_color: [255, 0, 0] },
  { entity_id: 'light.living_room' }
);

// Control multiple entities at once
await callService(connection, 'light', 'turn_off', {}, {
  entity_id: ['light.bedroom', 'light.kitchen'],
  area_id: 'living_room'
});
```

---

## 5. Device Control — Service Calls

### Via WebSocket
```json
{
  "id": 24,
  "type": "call_service",
  "domain": "light",
  "service": "turn_on",
  "service_data": {"brightness": 255, "color_name": "blue"},
  "target": {"entity_id": "light.kitchen"}
}
```

### Via REST
```bash
curl -H "Authorization: Bearer TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"entity_id": "light.kitchen", "brightness": 255}' \
     http://localhost:8123/api/services/light/turn_on
```

### Common Services for Phase 1

| Device Type | Service | Key Parameters |
|------------|---------|----------------|
| Lights | `light.turn_on` | `brightness`, `rgb_color`, `color_temp` |
| Lights | `light.turn_off` | — |
| Switches/Plugs | `switch.turn_on` / `switch.turn_off` / `switch.toggle` | — |
| Thermostat | `climate.set_temperature` | `temperature` |
| Thermostat | `climate.set_hvac_mode` | `hvac_mode`: heat/cool/auto/off |
| Camera | WebSocket `stream_camera` | Returns `hls_path`, `mjpeg_path` |
| Camera | `GET /api/camera_proxy/{id}` | Snapshot image |

### Targeting Multiple Entities
```javascript
await callService(connection, 'light', 'turn_off', {}, {
  entity_id: ['light.bedroom', 'light.kitchen'],
  area_id: 'living_room'  // all lights in an area
});
```

---

## 6. Camera Streaming

**Snapshot:** `GET /api/camera_proxy/{camera.entity_id}?time={timestamp}`

**Live stream via WebSocket:**
```json
{"id": 5, "type": "stream_camera", "data": {"camera_entity_id": "camera.front_door"}}
```
Response:
```json
{"hls_path": "/api/hls/.../playlist.m3u8", "mjpeg_path": "/api/camera_proxy_stream/..."}
```

For our dashboard:
- **MJPEG** — works in an `<img>` tag, simplest approach
- **HLS** — needs hls.js player, better quality/performance
- **Snapshot** — periodic refresh for low-bandwidth view

**Gotcha:** HLS requires the `stream` integration enabled in HA config.

---

## 7. Broadlink / IR Blaster (Phase 3 — Research Only)

The Broadlink integration auto-discovers RM4 Mini devices via broadcast. Creates a `remote.*` entity.

**Learning commands:**
```json
{
  "type": "call_service",
  "domain": "remote",
  "service": "learn_command",
  "service_data": {"device": "television", "command": "power"},
  "target": {"entity_id": "remote.bedroom"}
}
```

**Sending commands:**
```json
{
  "type": "call_service",
  "domain": "remote",
  "service": "send_command",
  "service_data": {
    "device": "television",
    "command": "power",
    "num_repeats": 1,
    "delay_secs": 0.4
  },
  "target": {"entity_id": "remote.bedroom"}
}
```

Can also send raw base64 codes: `"command": "b64:JgBGAJKVETkRORA6ERAREA..."`.

Codes are stored in HA's storage folder, grouped by device name.

---

## 8. Automations (Phase 2 — Research Only)

**Structure:** triggers → conditions → actions

```yaml
triggers:
  - trigger: state
    entity_id: binary_sensor.motion
    from: "off"
    to: "on"
conditions:
  - condition: time
    after: "20:00"
actions:
  - action: light.turn_on
    target:
      entity_id: light.kitchen
```

**Real-time trigger subscription via WebSocket:**
```json
{
  "id": 2,
  "type": "subscribe_trigger",
  "trigger": {
    "platform": "state",
    "entity_id": "binary_sensor.motion",
    "from": "off",
    "to": "on"
  }
}
```

For Phase 2, we'll use `subscribe_trigger` for real-time event monitoring and the REST/WebSocket automation APIs to create rules programmatically.

---

## 9. Docker Setup

```yaml
services:
  homeassistant:
    container_name: homeassistant
    image: "ghcr.io/home-assistant/home-assistant:stable"
    volumes:
      - ./ha-config:/config
      - /etc/localtime:/etc/localtime:ro
      - /run/dbus:/run/dbus:ro
    restart: unless-stopped
    privileged: true
    network_mode: host
    environment:
      TZ: Asia/Kuala_Lumpur
```

**Critical requirements:**
- `network_mode: host` — mandatory for mDNS/SSDP/DHCP discovery
- `privileged: true` — needed for USB device access (Zigbee dongles, etc.)
- `/run/dbus` mount — needed for Bluetooth discovery
- Since HA uses host networking, it binds directly to port **8123**

---

## 10. Key Gotchas & Limitations

1. **Host networking is non-negotiable** — bridge mode = no device discovery
2. **All states are strings** — `"23.5"` not `23.5`, `"on"` not `true`
3. **`unavailable` state** = device is offline/unreachable
4. **`unknown` state** = HA knows the entity but hasn't received data yet
5. **Entity ≠ Device** — one device (e.g., a smart plug) can have multiple entities (switch, power sensor, voltage sensor)
6. **Area override** — an entity's `area_id` takes precedence over its device's `area_id`
7. **Long-lived tokens are one-shot** — HA doesn't save them; lose it = generate a new one
8. **Camera HLS** requires the `stream` integration enabled in HA config
9. **Discovery requires onboarding** — first-time HA setup must complete before discovery works
10. **Use the JS WebSocket library** (`home-assistant-js-websocket`) — handles reconnection, auth, and entity subscriptions. Don't build a raw WebSocket client from scratch.

---

## Feature Mapping Table

| Our Feature (from onepager) | HA Concept | API/Method | Notes |
|-|-|-|-|
| **Auto-discover devices** | Zeroconf, SSDP, DHCP discovery built into HA | Automatic — HA handles internally | Requires `network_mode: host`. Devices appear in device registry after discovery. No code needed from us. |
| **Show device list with status** | Device Registry + Entity Registry + Entity States | WS: `config/device_registry/list` + `config/entity_registry/list` + `get_states` | Must combine all 3: device metadata (name, manufacturer, model) from device registry, entities linked via `device_id`, current state from states. MAC/IP from `connections` field. |
| **Real-time online/offline** | `state_changed` events on event bus | WS: `subscribe_events` (event_type: `state_changed`) or JS lib `subscribeEntities()` | Entity state = `unavailable` means offline. Use `subscribeEntities()` from JS lib for simplest approach — it auto-diffs and sends only changes. |
| **Toggle lights/switches** | Service calls: `light.turn_on/off`, `switch.toggle` | WS: `call_service` or JS lib `callService()` or REST: `POST /api/services/light/turn_on` | Pass `entity_id` in `target`. Can control by `area_id` too. Brightness/color via `service_data`. |
| **View camera feeds** | Camera entity + proxy/stream | REST: `GET /api/camera_proxy/{entity_id}` (snapshot) or WS: `stream_camera` → returns `mjpeg_path`/`hls_path` | MJPEG works in `<img>` tag. HLS needs hls.js player. Requires `stream` integration enabled for HLS. |
| **Adjust thermostat** | Climate service calls | `climate.set_temperature` (temp), `climate.set_hvac_mode` (mode) | State shows current temp. Attributes have `target_temperature`, `hvac_modes`, `min_temp`, `max_temp`. |
| **Room/area grouping** | Area Registry | WS: `config/area_registry/list` | Returns `area_id` + `name`. Devices link via `area_id`. Entities can override device area. Group devices by matching `area_id`. |
| **View sensor readings** | Sensor entity states | `get_states` → filter `sensor.*` entities | State = reading value (string). Attributes have `unit_of_measurement`, `device_class` (temperature, humidity, motion, etc.). |
| **Control AC via IR blaster (Phase 3)** | Broadlink integration → `remote.*` entity | `remote.send_command` (send), `remote.learn_command` (learn) | Broadlink auto-discovered. Codes stored by device name. Can send raw base64 or named commands. `num_repeats` and `delay_secs` params available. |
| **Create automations from AI (Phase 2)** | Automation: triggers → conditions → actions | WS: `subscribe_trigger` for real-time, REST automation endpoints for CRUD | Structure: `{triggers: [...], conditions: [...], actions: [...]}`. Can subscribe to specific triggers via WebSocket. AI generates the JSON structure, API creates the rule. |
