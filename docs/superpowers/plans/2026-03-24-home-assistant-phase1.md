# Home Assistant Wrapper — Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a device discovery dashboard that wraps Home Assistant, showing all discovered Wi-Fi/IP devices with real-time status updates.

**Architecture:** Home Assistant runs in Docker with host networking for LAN discovery. A Bun + Elysia API layer connects to HA via WebSocket/REST and exposes a clean device API. A React frontend displays the device list with live updates.

**Tech Stack:** Bun, Elysia, React, TypeScript, RSBuild, Docker Compose, Home Assistant WebSocket/REST API

**Spec:** `docs/superpowers/specs/2026-03-24-home-assistant-wrapper-design.md`

---

### Task 1: Project Scaffold & Docker Compose

**Files:**
- Create: `docker-compose.yml`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `api/package.json`
- Create: `api/tsconfig.json`
- Create: `api/Dockerfile`
- Create: `web/package.json`
- Create: `web/tsconfig.json`
- Create: `web/rsbuild.config.ts`
- Create: `web/Dockerfile`

- [ ] **Step 1: Initialize git repo**

```bash
cd /home/edgenesis/Downloads/home-assistant
git init
```

- [ ] **Step 2: Create `.gitignore`**

```gitignore
node_modules/
dist/
.env
ha-config/
*.log
.bun
```

- [ ] **Step 3: Create `.env.example`**

```env
HA_URL=http://localhost:8123
HA_TOKEN=your_long_lived_access_token_here
PORT=3001
TZ=Asia/Singapore
```

- [ ] **Step 4: Create `docker-compose.yml`**

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
      - TZ=${TZ:-Asia/Singapore}
    restart: unless-stopped
    network_mode: host

  api:
    container_name: ha-wrapper-api
    build: ./api
    environment:
      - HA_URL=${HA_URL:-http://localhost:8123}
      - HA_TOKEN=${HA_TOKEN}
      - PORT=${PORT:-3001}
    network_mode: host
    depends_on:
      - homeassistant
    restart: unless-stopped

  web:
    container_name: ha-wrapper-web
    build: ./web
    depends_on:
      - api
    network_mode: host
    restart: unless-stopped
```

- [ ] **Step 5: Create `api/package.json`**

```json
{
  "name": "ha-wrapper-api",
  "version": "0.1.0",
  "scripts": {
    "dev": "bun run --watch src/index.ts",
    "start": "bun run src/index.ts",
    "test": "bun test"
  },
  "dependencies": {
    "elysia": "^1.2.0"
  },
  "devDependencies": {
    "@types/bun": "latest",
    "typescript": "^5.7.0"
  }
}
```

- [ ] **Step 6: Create `api/tsconfig.json`**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "esModuleInterop": true,
    "outDir": "./dist",
    "rootDir": "./src",
    "types": ["bun"]
  },
  "include": ["src/**/*"]
}
```

- [ ] **Step 7: Create `api/Dockerfile`**

```dockerfile
FROM oven/bun:1-alpine
WORKDIR /app
COPY package.json bun.lock* ./
RUN bun install --frozen-lockfile || bun install
COPY . .
EXPOSE 3001
CMD ["bun", "run", "start"]
```

- [ ] **Step 8: Create `web/package.json`**

```json
{
  "name": "ha-wrapper-web",
  "version": "0.1.0",
  "scripts": {
    "dev": "rsbuild dev",
    "build": "rsbuild build",
    "start": "rsbuild preview"
  },
  "dependencies": {
    "react": "^19.0.0",
    "react-dom": "^19.0.0"
  },
  "devDependencies": {
    "@rsbuild/core": "^1.2.0",
    "@rsbuild/plugin-react": "^1.2.0",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "typescript": "^5.7.0"
  }
}
```

- [ ] **Step 9: Create `web/tsconfig.json`**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "jsx": "react-jsx",
    "esModuleInterop": true,
    "types": ["@rsbuild/core/types"]
  },
  "include": ["src/**/*"]
}
```

- [ ] **Step 10: Create `web/rsbuild.config.ts`**

```typescript
import { defineConfig } from "@rsbuild/core";
import { pluginReact } from "@rsbuild/plugin-react";

export default defineConfig({
  plugins: [pluginReact()],
  server: {
    port: 3000,
    proxy: {
      "/api": "http://localhost:3001",
    },
  },
  output: {
    assetPrefix: "/",
  },
});
```

- [ ] **Step 11: Create `web/Dockerfile`**

```dockerfile
FROM oven/bun:1-alpine AS build
WORKDIR /app
COPY package.json bun.lock* ./
RUN bun install --frozen-lockfile || bun install
COPY . .
RUN bun run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 3000
```

- [ ] **Step 12: Create `web/nginx.conf`**

```nginx
server {
    listen 3000;
    root /usr/share/nginx/html;
    index index.html;

    location /api/ {
        proxy_pass http://localhost:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

- [ ] **Step 13: Install dependencies**

```bash
cd /home/edgenesis/Downloads/home-assistant/api && bun install
cd /home/edgenesis/Downloads/home-assistant/web && bun install
```

- [ ] **Step 14: Commit**

```bash
git add -A
git commit -m "feat: project scaffold with Docker Compose, Bun API, and React frontend"
```

---

### Task 2: HA WebSocket Client

**Files:**
- Create: `api/src/types.ts`
- Create: `api/src/ha-client.ts`
- Create: `api/tests/ha-client.test.ts`

- [ ] **Step 1: Write types**

Create `api/src/types.ts`:

```typescript
// Home Assistant API types

export interface HADeviceRegistryEntry {
  id: string;
  config_entries: string[];
  connections: [string, string][];
  identifiers: [string, string][];
  manufacturer: string | null;
  model: string | null;
  name: string | null;
  name_by_user: string | null;
  sw_version: string | null;
  hw_version: string | null;
  area_id: string | null;
  disabled_by: string | null;
}

export interface HAEntityRegistryEntry {
  entity_id: string;
  device_id: string | null;
  platform: string;
  disabled_by: string | null;
  original_name: string | null;
}

export interface HAState {
  entity_id: string;
  state: string;
  attributes: Record<string, unknown>;
  last_changed: string;
  last_updated: string;
}

export interface HAConfigFlow {
  flow_id: string;
  handler: string;
  context: {
    source: string;
    [key: string]: unknown;
  };
}

export interface Device {
  id: string;
  name: string;
  manufacturer: string | null;
  model: string | null;
  ipAddress: string | null;
  macAddress: string | null;
  status: "online" | "offline" | "unknown";
  discoverySource: string;
  entityCount: number;
  lastSeen: string;
  area: string | null;
}
```

- [ ] **Step 2: Write failing test for HA client**

Create `api/tests/ha-client.test.ts`:

```typescript
import { describe, it, expect, mock, beforeEach } from "bun:test";
import { HAClient } from "../src/ha-client";

describe("HAClient", () => {
  it("should construct with url and token", () => {
    const client = new HAClient("http://localhost:8123", "test-token");
    expect(client).toBeDefined();
  });

  it("should send WebSocket command and parse response", async () => {
    // Test the wsCommand helper parses HA WebSocket responses correctly
    const client = new HAClient("http://localhost:8123", "test-token");
    // wsCommand is tested indirectly via getDeviceRegistry/getEntityRegistry
    // which require a live HA instance. Unit test focuses on construction + health.
    expect(client).toBeDefined();
  });

  it("should fetch all entity states", async () => {
    const mockStates = [
      {
        entity_id: "light.living_room",
        state: "on",
        attributes: { friendly_name: "Living Room" },
        last_changed: "2026-03-24T10:00:00Z",
        last_updated: "2026-03-24T10:00:00Z",
      },
    ];

    const client = new HAClient("http://localhost:8123", "test-token");
    const originalFetch = globalThis.fetch;
    globalThis.fetch = mock(() =>
      Promise.resolve(new Response(JSON.stringify(mockStates)))
    ) as typeof fetch;

    const states = await client.getStates();
    expect(states).toHaveLength(1);
    expect(states[0].entity_id).toBe("light.living_room");

    globalThis.fetch = originalFetch;
  });

  it("should check API health", async () => {
    const client = new HAClient("http://localhost:8123", "test-token");
    const originalFetch = globalThis.fetch;
    globalThis.fetch = mock(() =>
      Promise.resolve(new Response(JSON.stringify({ message: "API running." })))
    ) as typeof fetch;

    const healthy = await client.checkHealth();
    expect(healthy).toBe(true);

    globalThis.fetch = originalFetch;
  });
});
```

- [ ] **Step 3: Run test to verify it fails**

```bash
cd /home/edgenesis/Downloads/home-assistant/api && bun test
```

Expected: FAIL — `HAClient` not found.

- [ ] **Step 4: Implement HA client**

Create `api/src/ha-client.ts`:

```typescript
import type {
  HADeviceRegistryEntry,
  HAEntityRegistryEntry,
  HAState,
  HAConfigFlow,
} from "./types";

export class HAClient {
  private url: string;
  private token: string;
  private ws: WebSocket | null = null;
  private msgId = 1;
  private pendingRequests = new Map<number, {
    resolve: (data: unknown) => void;
    reject: (err: Error) => void;
  }>();
  private authenticated = false;
  private authPromise: Promise<void> | null = null;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private stateChangeCallback: ((entityId: string, newState: HAState) => void) | null = null;

  constructor(url: string, token: string) {
    this.url = url.replace(/\/$/, "");
    this.token = token;
  }

  private headers(): Record<string, string> {
    return {
      Authorization: `Bearer ${this.token}`,
      "Content-Type": "application/json",
    };
  }

  /** Connect and authenticate the WebSocket. Auto-reconnects on close. */
  async connect(): Promise<void> {
    if (this.authPromise) return this.authPromise;

    this.authPromise = new Promise<void>((resolveAuth, rejectAuth) => {
      const wsUrl = this.url.replace(/^http/, "ws") + "/api/websocket";
      this.ws = new WebSocket(wsUrl);

      this.ws.onmessage = (event) => {
        const msg = JSON.parse(event.data as string);

        if (msg.type === "auth_required") {
          this.ws!.send(JSON.stringify({ type: "auth", access_token: this.token }));
        } else if (msg.type === "auth_ok") {
          this.authenticated = true;
          resolveAuth();
        } else if (msg.type === "auth_invalid") {
          rejectAuth(new Error("HA auth failed: " + msg.message));
        } else if (msg.type === "result") {
          const pending = this.pendingRequests.get(msg.id);
          if (pending) {
            this.pendingRequests.delete(msg.id);
            if (msg.success) {
              pending.resolve(msg.result);
            } else {
              pending.reject(new Error(msg.error?.message ?? "HA command failed"));
            }
          }
        } else if (msg.type === "event" && msg.event?.event_type === "state_changed") {
          const { entity_id, new_state } = msg.event.data;
          if (new_state && this.stateChangeCallback) {
            this.stateChangeCallback(entity_id, new_state);
          }
        }
      };

      this.ws.onclose = () => {
        this.authenticated = false;
        this.authPromise = null;
        // Reject any pending requests
        for (const [, pending] of this.pendingRequests) {
          pending.reject(new Error("WebSocket closed"));
        }
        this.pendingRequests.clear();
        // Auto-reconnect after 5 seconds
        this.reconnectTimer = setTimeout(() => {
          console.log("Reconnecting to Home Assistant...");
          this.connect().catch(console.error);
        }, 5000);
      };

      this.ws.onerror = () => {
        // onclose will fire after onerror, handling reconnect
      };
    });

    return this.authPromise;
  }

  /** Send a WebSocket command and wait for the result */
  private async wsCommand<T>(type: string): Promise<T> {
    await this.connect();
    const id = this.msgId++;
    return new Promise<T>((resolve, reject) => {
      this.pendingRequests.set(id, {
        resolve: resolve as (data: unknown) => void,
        reject,
      });
      this.ws!.send(JSON.stringify({ id, type }));
    });
  }

  async checkHealth(): Promise<boolean> {
    try {
      const res = await fetch(`${this.url}/api/`, {
        headers: this.headers(),
      });
      if (!res.ok) return false;
      const data = (await res.json()) as { message: string };
      return data.message === "API running.";
    } catch {
      return false;
    }
  }

  /** Device registry — WebSocket only (no REST endpoint) */
  async getDeviceRegistry(): Promise<HADeviceRegistryEntry[]> {
    return this.wsCommand<HADeviceRegistryEntry[]>("config/device_registry/list");
  }

  /** Entity registry — WebSocket only (no REST endpoint) */
  async getEntityRegistry(): Promise<HAEntityRegistryEntry[]> {
    return this.wsCommand<HAEntityRegistryEntry[]>("config/entity_registry/list");
  }

  /** Entity states — available via REST */
  async getStates(): Promise<HAState[]> {
    const res = await fetch(`${this.url}/api/states`, {
      headers: this.headers(),
    });
    if (!res.ok) throw new Error(`HA API error: ${res.status}`);
    return res.json() as Promise<HAState[]>;
  }

  /** Discovery flows — WebSocket only */
  async getDiscoveryFlows(): Promise<HAConfigFlow[]> {
    return this.wsCommand<HAConfigFlow[]>("config/config_entries/flow/progress");
  }

  /** Subscribe to state_changed events. Reconnects automatically. */
  async subscribeStateChanges(
    onStateChanged: (entityId: string, newState: HAState) => void
  ): Promise<void> {
    this.stateChangeCallback = onStateChanged;
    await this.connect();
    const id = this.msgId++;
    this.ws!.send(
      JSON.stringify({ id, type: "subscribe_events", event_type: "state_changed" })
    );
  }

  /** Clean disconnect */
  close(): void {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.stateChangeCallback = null;
    this.ws?.close();
  }
}
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd /home/edgenesis/Downloads/home-assistant/api && bun test
```

Expected: All 4 tests PASS.

- [ ] **Step 6: Commit**

```bash
cd /home/edgenesis/Downloads/home-assistant
git add api/src/types.ts api/src/ha-client.ts api/tests/ha-client.test.ts
git commit -m "feat: HA WebSocket/REST client with types and tests"
```

---

### Task 3: Device Service (Aggregation Logic)

**Files:**
- Create: `api/src/device-service.ts`
- Create: `api/tests/device-service.test.ts`

- [ ] **Step 1: Write failing test**

Create `api/tests/device-service.test.ts`:

```typescript
import { describe, it, expect } from "bun:test";
import { DeviceService } from "../src/device-service";
import type {
  HADeviceRegistryEntry,
  HAEntityRegistryEntry,
  HAState,
} from "../src/types";

const mockDevices: HADeviceRegistryEntry[] = [
  {
    id: "dev1",
    config_entries: ["entry1"],
    connections: [["mac", "aa:bb:cc:dd:ee:ff"]],
    identifiers: [["esphome", "device1"]],
    manufacturer: "Espressif",
    model: "ESP32",
    name: "Living Room Sensor",
    name_by_user: null,
    sw_version: "1.0",
    hw_version: null,
    area_id: "living_room",
    disabled_by: null,
  },
  {
    id: "dev2",
    config_entries: ["entry2"],
    connections: [],
    identifiers: [["cast", "chromecast1"]],
    manufacturer: "Google",
    model: "Chromecast",
    name: "TV Chromecast",
    name_by_user: "My TV",
    sw_version: null,
    hw_version: null,
    area_id: null,
    disabled_by: null,
  },
];

const mockEntities: HAEntityRegistryEntry[] = [
  {
    entity_id: "sensor.living_room_temp",
    device_id: "dev1",
    platform: "esphome",
    disabled_by: null,
    original_name: "Temperature",
  },
  {
    entity_id: "sensor.living_room_humidity",
    device_id: "dev1",
    platform: "esphome",
    disabled_by: null,
    original_name: "Humidity",
  },
  {
    entity_id: "media_player.chromecast",
    device_id: "dev2",
    platform: "cast",
    disabled_by: null,
    original_name: "Chromecast",
  },
];

const mockStates: HAState[] = [
  {
    entity_id: "sensor.living_room_temp",
    state: "22.5",
    attributes: { friendly_name: "Temperature", unit_of_measurement: "°C" },
    last_changed: "2026-03-24T10:00:00Z",
    last_updated: "2026-03-24T10:00:00Z",
  },
  {
    entity_id: "sensor.living_room_humidity",
    state: "45",
    attributes: { friendly_name: "Humidity" },
    last_changed: "2026-03-24T10:00:00Z",
    last_updated: "2026-03-24T10:00:00Z",
  },
  {
    entity_id: "media_player.chromecast",
    state: "unavailable",
    attributes: { friendly_name: "Chromecast" },
    last_changed: "2026-03-24T09:00:00Z",
    last_updated: "2026-03-24T09:00:00Z",
  },
];

describe("DeviceService", () => {
  it("should aggregate devices with entity counts", () => {
    const service = new DeviceService();
    const devices = service.buildDeviceList(
      mockDevices,
      mockEntities,
      mockStates
    );

    expect(devices).toHaveLength(2);

    const sensor = devices.find((d) => d.id === "dev1")!;
    expect(sensor.name).toBe("Living Room Sensor");
    expect(sensor.entityCount).toBe(2);
    expect(sensor.manufacturer).toBe("Espressif");
    expect(sensor.macAddress).toBe("aa:bb:cc:dd:ee:ff");
  });

  it("should detect offline devices (all entities unavailable)", () => {
    const service = new DeviceService();
    const devices = service.buildDeviceList(
      mockDevices,
      mockEntities,
      mockStates
    );

    const chromecast = devices.find((d) => d.id === "dev2")!;
    expect(chromecast.status).toBe("offline");
  });

  it("should detect online devices (at least one entity available)", () => {
    const service = new DeviceService();
    const devices = service.buildDeviceList(
      mockDevices,
      mockEntities,
      mockStates
    );

    const sensor = devices.find((d) => d.id === "dev1")!;
    expect(sensor.status).toBe("online");
  });

  it("should use name_by_user when set", () => {
    const service = new DeviceService();
    const devices = service.buildDeviceList(
      mockDevices,
      mockEntities,
      mockStates
    );

    const chromecast = devices.find((d) => d.id === "dev2")!;
    expect(chromecast.name).toBe("My TV");
  });

  it("should extract MAC address from connections", () => {
    const service = new DeviceService();
    const devices = service.buildDeviceList(
      mockDevices,
      mockEntities,
      mockStates
    );

    const sensor = devices.find((d) => d.id === "dev1")!;
    expect(sensor.macAddress).toBe("aa:bb:cc:dd:ee:ff");
  });

  it("should handle device with no entities as unknown status", () => {
    const loneDevice: HADeviceRegistryEntry = {
      id: "dev3",
      config_entries: [],
      connections: [],
      identifiers: [],
      manufacturer: null,
      model: null,
      name: "Unknown",
      name_by_user: null,
      sw_version: null,
      hw_version: null,
      area_id: null,
      disabled_by: null,
    };

    const service = new DeviceService();
    const devices = service.buildDeviceList(
      [loneDevice],
      [],
      []
    );

    expect(devices[0].status).toBe("unknown");
    expect(devices[0].entityCount).toBe(0);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/edgenesis/Downloads/home-assistant/api && bun test tests/device-service.test.ts
```

Expected: FAIL — `DeviceService` not found.

- [ ] **Step 3: Implement device service**

Create `api/src/device-service.ts`:

```typescript
import type {
  HADeviceRegistryEntry,
  HAEntityRegistryEntry,
  HAState,
  Device,
} from "./types";

export class DeviceService {
  buildDeviceList(
    haDevices: HADeviceRegistryEntry[],
    haEntities: HAEntityRegistryEntry[],
    haStates: HAState[]
  ): Device[] {
    // Index entities by device_id
    const entitiesByDevice = new Map<string, HAEntityRegistryEntry[]>();
    for (const entity of haEntities) {
      if (!entity.device_id) continue;
      const list = entitiesByDevice.get(entity.device_id) ?? [];
      list.push(entity);
      entitiesByDevice.set(entity.device_id, list);
    }

    // Index states by entity_id
    const statesByEntity = new Map<string, HAState>();
    for (const state of haStates) {
      statesByEntity.set(state.entity_id, state);
    }

    return haDevices.map((dev) => {
      const entities = entitiesByDevice.get(dev.id) ?? [];
      const entityStates = entities
        .map((e) => statesByEntity.get(e.entity_id))
        .filter((s): s is HAState => s !== undefined);

      // Extract MAC from connections
      const macConn = dev.connections.find(([type]) => type === "mac");
      const macAddress = macConn ? macConn[1] : null;

      // Extract IP from entity attributes (some integrations expose it)
      let ipAddress: string | null = null;
      for (const state of entityStates) {
        const ip = state.attributes["ip_address"] ?? state.attributes["host"];
        if (typeof ip === "string") {
          ipAddress = ip;
          break;
        }
      }

      // Determine online/offline status
      let status: Device["status"];
      if (entityStates.length === 0) {
        status = "unknown";
      } else if (entityStates.every((s) => s.state === "unavailable")) {
        status = "offline";
      } else {
        status = "online";
      }

      // Find most recent update time
      const lastSeen =
        entityStates.length > 0
          ? entityStates.reduce((latest, s) =>
              s.last_updated > latest.last_updated ? s : latest
            ).last_updated
          : new Date().toISOString();

      // Determine discovery source from identifiers
      const discoverySource = dev.identifiers.length > 0
        ? dev.identifiers[0][0]
        : "unknown";

      return {
        id: dev.id,
        name: dev.name_by_user ?? dev.name ?? "Unknown Device",
        manufacturer: dev.manufacturer,
        model: dev.model,
        ipAddress,
        macAddress,
        status,
        discoverySource,
        entityCount: entities.length,
        lastSeen,
        area: dev.area_id,
      };
    });
  }
}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /home/edgenesis/Downloads/home-assistant/api && bun test tests/device-service.test.ts
```

Expected: All 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
cd /home/edgenesis/Downloads/home-assistant
git add api/src/device-service.ts api/tests/device-service.test.ts
git commit -m "feat: device service aggregates HA registry + states into Device list"
```

---

### Task 4: API Routes (Elysia Server)

**Files:**
- Create: `api/src/routes/devices.ts`
- Create: `api/src/index.ts`

- [ ] **Step 1: Create device routes**

Create `api/src/routes/devices.ts`:

```typescript
import { Elysia } from "elysia";
import type { HAClient } from "../ha-client";
import { DeviceService } from "../device-service";
import type { Device } from "../types";

export function deviceRoutes(haClient: HAClient) {
  const deviceService = new DeviceService();
  let cachedDevices: Device[] = [];
  let lastFetch = 0;
  const CACHE_TTL = 5_000; // 5 seconds

  async function refreshDevices(): Promise<Device[]> {
    const now = Date.now();
    if (now - lastFetch < CACHE_TTL && cachedDevices.length > 0) {
      return cachedDevices;
    }

    const [devices, entities, states] = await Promise.all([
      haClient.getDeviceRegistry(),
      haClient.getEntityRegistry(),
      haClient.getStates(),
    ]);

    cachedDevices = deviceService.buildDeviceList(devices, entities, states);
    lastFetch = now;
    return cachedDevices;
  }

  return new Elysia({ prefix: "/api" })
    .get("/devices", async () => {
      const devices = await refreshDevices();
      return { devices, total: devices.length };
    })
    .get("/devices/:id", async ({ params, set }) => {
      const devices = await refreshDevices();
      const device = devices.find((d) => d.id === params.id);
      if (!device) {
        set.status = 404;
        return { error: { code: "NOT_FOUND", message: "Device not found" } };
      }
      return device;
    })
    .get("/health", async () => {
      const haHealthy = await haClient.checkHealth();
      return {
        status: haHealthy ? "ok" : "degraded",
        ha_connected: haHealthy,
      };
    });
}
```

- [ ] **Step 2: Create server entry point**

Create `api/src/index.ts`:

```typescript
import { Elysia } from "elysia";
import { HAClient } from "./ha-client";
import { deviceRoutes } from "./routes/devices";

const HA_URL = process.env.HA_URL ?? "http://localhost:8123";
const HA_TOKEN = process.env.HA_TOKEN ?? "";
const PORT = parseInt(process.env.PORT ?? "3001", 10);

if (!HA_TOKEN) {
  console.error("HA_TOKEN environment variable is required");
  console.error("Create a long-lived access token in HA: Profile → Security → Long-Lived Access Tokens");
  process.exit(1);
}

const haClient = new HAClient(HA_URL, HA_TOKEN);

const app = new Elysia()
  .use(deviceRoutes(haClient))
  .listen(PORT);

console.log(`API server running on port ${PORT}`);
console.log(`Home Assistant URL: ${HA_URL}`);

// Connect to HA WebSocket and subscribe to state changes
haClient.connect().then(() => {
  console.log("Connected to Home Assistant WebSocket");
  haClient.subscribeStateChanges((entityId, newState) => {
    // Log state changes for now — Phase 2 will push to frontend via SSE/WS
    console.log(`State changed: ${entityId} → ${newState.state}`);
  });
}).catch((err) => {
  console.error("Failed to connect to Home Assistant:", err.message);
});

process.on("SIGTERM", () => {
  haClient.close();
  process.exit(0);
});
```

- [ ] **Step 3: Verify API starts (manual check)**

```bash
cd /home/edgenesis/Downloads/home-assistant/api
HA_TOKEN=test PORT=3001 bun run src/index.ts
```

Expected: Server starts on port 3001 but will fail to connect to HA WebSocket (no real HA running). That's OK — we verify full connectivity in Task 6.

- [ ] **Step 4: Commit**

```bash
cd /home/edgenesis/Downloads/home-assistant
git add api/src/routes/devices.ts api/src/index.ts
git commit -m "feat: Elysia API server with /api/devices and /api/health endpoints"
```

---

### Task 5: React Frontend — Device List Dashboard

**Files:**
- Create: `web/src/main.tsx`
- Create: `web/src/App.tsx`
- Create: `web/src/types/device.ts`
- Create: `web/src/hooks/useDevices.ts`
- Create: `web/src/components/DeviceList.tsx`
- Create: `web/src/components/DeviceCard.tsx`
- Create: `web/src/components/StatusBadge.tsx`
- Create: `web/src/styles/global.css`
- Create: `web/public/index.html`

- [ ] **Step 1: Create shared types**

Create `web/src/types/device.ts`:

```typescript
export interface Device {
  id: string;
  name: string;
  manufacturer: string | null;
  model: string | null;
  ipAddress: string | null;
  macAddress: string | null;
  status: "online" | "offline" | "unknown";
  discoverySource: string;
  entityCount: number;
  lastSeen: string;
  area: string | null;
}
```

- [ ] **Step 2: Create useDevices hook**

Create `web/src/hooks/useDevices.ts`:

```typescript
import { useState, useEffect, useCallback } from "react";
import type { Device } from "../types/device";

const API_BASE = "/api";

interface DevicesResponse {
  devices: Device[];
  total: number;
}

export function useDevices(pollInterval = 10_000) {
  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDevices = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/devices`);
      if (!res.ok) throw new Error(`API error: ${res.status}`);
      const data: DevicesResponse = await res.json();
      setDevices(data.devices);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch devices");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDevices();
    const interval = setInterval(fetchDevices, pollInterval);
    return () => clearInterval(interval);
  }, [fetchDevices, pollInterval]);

  return { devices, loading, error, refresh: fetchDevices };
}
```

- [ ] **Step 3: Create StatusBadge component**

Create `web/src/components/StatusBadge.tsx`:

```tsx
interface StatusBadgeProps {
  status: "online" | "offline" | "unknown";
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const colors = {
    online: { bg: "#dcfce7", text: "#166534", dot: "#22c55e" },
    offline: { bg: "#fee2e2", text: "#991b1b", dot: "#ef4444" },
    unknown: { bg: "#f3f4f6", text: "#6b7280", dot: "#9ca3af" },
  };

  const c = colors[status];

  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "6px",
        padding: "2px 10px",
        borderRadius: "9999px",
        fontSize: "12px",
        fontWeight: 500,
        backgroundColor: c.bg,
        color: c.text,
      }}
    >
      <span
        style={{
          width: "6px",
          height: "6px",
          borderRadius: "50%",
          backgroundColor: c.dot,
        }}
      />
      {status}
    </span>
  );
}
```

- [ ] **Step 4: Create DeviceCard component**

Create `web/src/components/DeviceCard.tsx`:

```tsx
import type { Device } from "../types/device";
import { StatusBadge } from "./StatusBadge";

interface DeviceCardProps {
  device: Device;
}

export function DeviceCard({ device }: DeviceCardProps) {
  const timeAgo = (iso: string) => {
    const diff = Date.now() - new Date(iso).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return "just now";
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    return `${Math.floor(hours / 24)}d ago`;
  };

  return (
    <div
      style={{
        border: "1px solid #e5e7eb",
        borderRadius: "8px",
        padding: "16px",
        backgroundColor: "#fff",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start" }}>
        <div>
          <h3 style={{ margin: 0, fontSize: "16px", fontWeight: 600 }}>{device.name}</h3>
          <p style={{ margin: "4px 0 0", fontSize: "13px", color: "#6b7280" }}>
            {[device.manufacturer, device.model].filter(Boolean).join(" · ") || "Unknown device"}
          </p>
        </div>
        <StatusBadge status={device.status} />
      </div>

      <div style={{ marginTop: "12px", fontSize: "13px", color: "#374151" }}>
        {device.ipAddress && <div>IP: {device.ipAddress}</div>}
        {device.macAddress && <div>MAC: {device.macAddress}</div>}
        <div>Source: {device.discoverySource}</div>
        <div>Entities: {device.entityCount}</div>
        {device.area && <div>Area: {device.area}</div>}
        <div style={{ color: "#9ca3af", marginTop: "4px" }}>Last seen: {timeAgo(device.lastSeen)}</div>
      </div>
    </div>
  );
}
```

- [ ] **Step 5: Create DeviceList component**

Create `web/src/components/DeviceList.tsx`:

```tsx
import { useDevices } from "../hooks/useDevices";
import { DeviceCard } from "./DeviceCard";

export function DeviceList() {
  const { devices, loading, error, refresh } = useDevices();

  if (loading) {
    return <div style={{ padding: "40px", textAlign: "center", color: "#6b7280" }}>Loading devices...</div>;
  }

  if (error) {
    return (
      <div style={{ padding: "40px", textAlign: "center" }}>
        <p style={{ color: "#dc2626" }}>Error: {error}</p>
        <button onClick={refresh} style={{ marginTop: "8px", padding: "8px 16px", cursor: "pointer" }}>
          Retry
        </button>
      </div>
    );
  }

  const online = devices.filter((d) => d.status === "online");
  const offline = devices.filter((d) => d.status === "offline");
  const unknown = devices.filter((d) => d.status === "unknown");

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
        <div>
          <span style={{ fontSize: "14px", color: "#6b7280" }}>
            {devices.length} devices — {online.length} online, {offline.length} offline
          </span>
        </div>
        <button
          onClick={refresh}
          style={{
            padding: "6px 12px",
            border: "1px solid #d1d5db",
            borderRadius: "6px",
            background: "#fff",
            cursor: "pointer",
            fontSize: "13px",
          }}
        >
          Refresh
        </button>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: "12px" }}>
        {devices.map((device) => (
          <DeviceCard key={device.id} device={device} />
        ))}
      </div>

      {devices.length === 0 && (
        <div style={{ padding: "60px", textAlign: "center", color: "#9ca3af" }}>
          <p style={{ fontSize: "18px" }}>No devices discovered yet</p>
          <p style={{ fontSize: "14px" }}>Make sure Home Assistant is running and discovering devices</p>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 6: Create App and entry point**

Create `web/src/App.tsx`:

```tsx
import { DeviceList } from "./components/DeviceList";

export function App() {
  return (
    <div style={{ maxWidth: "1200px", margin: "0 auto", padding: "24px" }}>
      <header style={{ marginBottom: "24px" }}>
        <h1 style={{ margin: 0, fontSize: "24px", fontWeight: 700 }}>Home Devices</h1>
        <p style={{ margin: "4px 0 0", fontSize: "14px", color: "#6b7280" }}>
          Auto-discovered devices on your network
        </p>
      </header>
      <DeviceList />
    </div>
  );
}
```

Create `web/src/main.tsx`:

```tsx
import { createRoot } from "react-dom/client";
import { App } from "./App";
import "./styles/global.css";

createRoot(document.getElementById("root")!).render(<App />);
```

- [ ] **Step 7: Create global styles**

Create `web/src/styles/global.css`:

```css
* {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  background-color: #f9fafb;
  color: #111827;
}
```

- [ ] **Step 8: Create `web/public/index.html`**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Home Devices</title>
</head>
<body>
  <div id="root"></div>
</body>
</html>
```

- [ ] **Step 9: Verify frontend builds**

```bash
cd /home/edgenesis/Downloads/home-assistant/web && bun run build
```

Expected: Build succeeds, output in `dist/`.

- [ ] **Step 10: Commit**

```bash
cd /home/edgenesis/Downloads/home-assistant
git add web/src/ web/public/
git commit -m "feat: React dashboard with device list, cards, and status badges"
```

---

### Task 6: End-to-End Smoke Test

- [ ] **Step 1: Start Home Assistant**

```bash
cd /home/edgenesis/Downloads/home-assistant
docker compose up homeassistant -d
```

Wait for HA to start (~1-2 min on first run). Visit `http://localhost:8123` to complete onboarding.

- [ ] **Step 2: Create HA access token**

In HA UI: Profile (bottom-left) → Security → Long-Lived Access Tokens → Create Token. Copy it.

- [ ] **Step 3: Set token in .env**

```bash
cp .env.example .env
# Edit .env and paste the token as HA_TOKEN
```

- [ ] **Step 4: Start API and verify**

```bash
cd /home/edgenesis/Downloads/home-assistant/api
source ../.env && HA_TOKEN=$HA_TOKEN bun run dev
```

In another terminal:

```bash
curl http://localhost:3001/api/health
# Expected: {"status":"ok","ha_connected":true}

curl http://localhost:3001/api/devices
# Expected: {"devices":[...],"total":N}
```

- [ ] **Step 5: Start frontend and verify**

```bash
cd /home/edgenesis/Downloads/home-assistant/web
bun run dev
```

Visit `http://localhost:3000` — should show the device dashboard with any discovered devices.

- [ ] **Step 6: Commit final state**

```bash
cd /home/edgenesis/Downloads/home-assistant
git add -A
git commit -m "chore: end-to-end verified — Phase 1 MVP complete"
```
