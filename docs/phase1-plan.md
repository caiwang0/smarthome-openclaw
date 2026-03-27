# Phase 1 MVP — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a three-service Docker stack (Home Assistant + Elysia API + React dashboard) that auto-discovers smart home devices, shows them with live status, and provides basic control — all organized by room.

**Architecture:** Home Assistant runs with host networking for device discovery. An Elysia/Bun API service connects to HA via WebSocket, aggregates device/entity/area registries into a unified device list, and exposes REST endpoints. A React SPA (served by nginx) polls the API every 10 seconds and renders device cards with controls.

**Tech Stack:** Docker Compose, Home Assistant (stable), Bun + Elysia (API), React + TypeScript + Tailwind CSS (dashboard), home-assistant-js-websocket (HA client), nginx (static serving)

**Issue Document:** `/home/edgenesis/Downloads/home-assistant/docs/phase1-issues.md`

---

## File Structure

```
home-assistant/
├── docker-compose.yml                    # All 3 services
├── .env.example                          # Template for env vars
├── ha-config/                            # HA persistent config (volume mount)
│
├── api/                                  # Elysia/Bun API service
│   ├── Dockerfile                        # Bun runtime container
│   ├── package.json                      # Dependencies
│   ├── tsconfig.json                     # TypeScript config
│   └── src/
│       ├── index.ts                      # Elysia app entry point — mounts routes, starts server
│       ├── ha-client.ts                  # WebSocket connection to HA — auth, reconnect, raw commands
│       ├── device-aggregator.ts          # Combines 3 registries + states → unified device list
│       ├── types.ts                      # Shared TypeScript types for devices, entities, areas
│       └── routes/
│           ├── devices.ts                # GET /api/devices, GET /api/devices/:id
│           ├── areas.ts                  # GET /api/areas
│           ├── services.ts               # POST /api/services/:domain/:service
│           └── camera.ts                 # GET /api/camera/:entity_id/snapshot
│
├── dashboard/                            # React dashboard
│   ├── Dockerfile                        # Multi-stage: build with Node, serve with nginx
│   ├── nginx.conf                        # nginx config with API proxy
│   ├── package.json                      # Dependencies
│   ├── tsconfig.json                     # TypeScript config
│   ├── tailwind.config.js                # Tailwind CSS config
│   ├── index.html                        # Vite entry HTML
│   ├── vite.config.ts                    # Vite config
│   ├── postcss.config.js                 # PostCSS config for Tailwind
│   └── src/
│       ├── main.tsx                      # React entry point
│       ├── index.css                     # Tailwind base imports
│       ├── App.tsx                       # Root component — layout, area tabs, polling
│       ├── api.ts                        # API client — fetch devices, areas, call services
│       ├── types.ts                      # TypeScript types (mirrors API types)
│       ├── hooks/
│       │   ├── useDevices.ts             # Polls GET /api/devices every 10s
│       │   └── useAreas.ts              # Fetches areas once on mount
│       └── components/
│           ├── DeviceCard.tsx            # Base card — name, status badge, manufacturer, IP/MAC
│           ├── LightCard.tsx             # Light control — toggle + brightness slider
│           ├── SwitchCard.tsx            # Switch control — on/off toggle
│           ├── ClimateCard.tsx           # Thermostat — temp controls + mode selector
│           ├── CameraCard.tsx            # Camera snapshot + enlarged view modal
│           ├── SensorCard.tsx            # Sensor reading — value + unit + icon
│           ├── AreaFilter.tsx            # Area tab bar for filtering
│           ├── StatusBadge.tsx           # Color-coded online/offline/unknown badge
│           ├── DeviceGrid.tsx            # Groups cards by area, renders grid
│           └── NotificationToast.tsx     # Toast for new device notifications
│
└── docs/                                 # Documentation (already exists)
    ├── ha-research.md
    ├── ha-research-prompt.md
    ├── onepager.md
    ├── phase1-issues.md
    └── phase1-plan.md (this file)
```

---

## Implementation Phases

The plan follows the dependency chain: **Infrastructure → Backend Core → Backend API → Frontend Core → Frontend Controls → Polish**.

---

## Phase A: Infrastructure (P1)

### Task 1: Docker Compose and Project Scaffolding

**Covers:** P1 (Docker Compose Multi-Service Setup)

**Files:**
- Create: `docker-compose.yml`
- Create: `.env.example`
- Create: `api/Dockerfile`
- Create: `api/package.json`
- Create: `api/tsconfig.json`
- Create: `api/src/index.ts`
- Create: `dashboard/Dockerfile`
- Create: `dashboard/package.json`
- Create: `dashboard/tsconfig.json`
- Create: `dashboard/vite.config.ts`
- Create: `dashboard/tailwind.config.js`
- Create: `dashboard/index.html`
- Create: `dashboard/nginx.conf`
- Create: `dashboard/src/main.tsx`
- Create: `dashboard/src/App.tsx`

- [ ] **Step 1: Create `.env.example`**

```env
# Home Assistant
HA_URL=http://localhost:8123
HA_TOKEN=your_long_lived_access_token_here

# API
API_PORT=3001

# Timezone
TZ=Asia/Kuala_Lumpur
```

- [ ] **Step 2: Create `docker-compose.yml`**

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
      TZ: ${TZ:-Asia/Kuala_Lumpur}

  api:
    container_name: smarthub-api
    build:
      context: ./api
      dockerfile: Dockerfile
    restart: unless-stopped
    network_mode: host
    environment:
      HA_URL: ${HA_URL:-http://localhost:8123}
      HA_TOKEN: ${HA_TOKEN}
      API_PORT: ${API_PORT:-3001}
    depends_on:
      - homeassistant

  dashboard:
    container_name: smarthub-dashboard
    build:
      context: ./dashboard
      dockerfile: Dockerfile
    restart: unless-stopped
    network_mode: host
    depends_on:
      - api
```

- [ ] **Step 3: Create API service scaffold**

`api/package.json`:
```json
{
  "name": "smarthub-api",
  "version": "0.1.0",
  "scripts": {
    "dev": "bun run --watch src/index.ts",
    "start": "bun run src/index.ts"
  },
  "dependencies": {
    "elysia": "^1.2.0",
    "home-assistant-js-websocket": "^9.4.0"
  },
  "devDependencies": {
    "@types/bun": "latest",
    "typescript": "^5.7.0"
  }
}
```

`api/tsconfig.json`:
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "outDir": "./dist",
    "rootDir": "./src",
    "types": ["bun"]
  },
  "include": ["src/**/*"]
}
```

`api/Dockerfile`:
```dockerfile
FROM oven/bun:1 AS base
WORKDIR /app
COPY package.json bun.lock* ./
RUN bun install --frozen-lockfile || bun install
COPY . .
EXPOSE 3001
CMD ["bun", "run", "src/index.ts"]
```

`api/src/index.ts` (minimal hello world):
```typescript
import { Elysia } from "elysia";

const app = new Elysia()
  .get("/api/health", () => ({ status: "ok" }))
  .listen(Number(process.env.API_PORT) || 3001);

console.log(`API running on port ${app.server?.port}`);
```

- [ ] **Step 4: Create dashboard scaffold**

`dashboard/package.json`:
```json
{
  "name": "smarthub-dashboard",
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^19.0.0",
    "react-dom": "^19.0.0"
  },
  "devDependencies": {
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "@vitejs/plugin-react": "^4.3.0",
    "autoprefixer": "^10.4.20",
    "postcss": "^8.4.49",
    "tailwindcss": "^3.4.0",
    "typescript": "^5.7.0",
    "vite": "^6.0.0"
  }
}
```

`dashboard/tsconfig.json`:
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "outDir": "./dist",
    "rootDir": "./src"
  },
  "include": ["src/**/*"]
}
```

`dashboard/vite.config.ts`:
```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      "/api": "http://localhost:3001",
    },
  },
});
```

`dashboard/tailwind.config.js`:
```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: { extend: {} },
  plugins: [],
};
```

`dashboard/index.html`:
```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>SmartHub Dashboard</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

`dashboard/src/main.tsx`:
```tsx
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

`dashboard/src/index.css`:
```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

`dashboard/postcss.config.js`:
```javascript
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
```

`dashboard/src/App.tsx`:
```tsx
export default function App() {
  return (
    <div className="min-h-screen bg-gray-950 text-white p-6">
      <h1 className="text-2xl font-bold">SmartHub Dashboard</h1>
      <p className="text-gray-400 mt-2">Loading devices...</p>
    </div>
  );
}
```

`dashboard/nginx.conf`:
```nginx
server {
    listen 3000;
    root /usr/share/nginx/html;
    index index.html;

    location /api/ {
        proxy_pass http://localhost:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

`dashboard/Dockerfile`:
```dockerfile
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]
```

- [ ] **Step 5: Install dependencies locally and verify builds**

```bash
cd /home/edgenesis/Downloads/home-assistant/api && bun install
cd /home/edgenesis/Downloads/home-assistant/dashboard && npm install
```

- [ ] **Step 6: Verify API starts**

```bash
cd /home/edgenesis/Downloads/home-assistant/api && bun run src/index.ts &
curl http://localhost:3001/api/health
# Expected: {"status":"ok"}
```

- [ ] **Step 7: Verify dashboard builds**

```bash
cd /home/edgenesis/Downloads/home-assistant/dashboard && npm run build
# Expected: vite build succeeds, output in dist/
```

- [ ] **Step 8: Commit**

```bash
git add docker-compose.yml .env.example api/ dashboard/
git commit -m "feat: scaffold Docker Compose, Elysia API, and React dashboard"
```

---

## Phase B: Backend Core (P2, P3, P4)

### Task 2: HA WebSocket Client

**Covers:** P2 (HA WebSocket Client with Authentication)

**Files:**
- Create: `api/src/ha-client.ts`
- Create: `api/src/types.ts`
- Modify: `api/src/index.ts`

- [ ] **Step 1: Create shared types**

`api/src/types.ts`:
```typescript
// ---- HA Registry Types (raw from WebSocket) ----

export interface HADevice {
  id: string;
  name: string | null;
  name_by_user: string | null;
  manufacturer: string | null;
  model: string | null;
  model_id: string | null;
  sw_version: string | null;
  hw_version: string | null;
  area_id: string | null;
  config_entries: string[];
  connections: [string, string][]; // e.g., [["mac", "AA:BB:CC:DD:EE:FF"]]
  identifiers: [string, string][]; // e.g., [["hue", "abc123"]]
  via_device_id: string | null;
  disabled_by: string | null;
}

export interface HAEntity {
  entity_id: string;
  device_id: string | null;
  area_id: string | null;
  platform: string;
  disabled_by: string | null;
  hidden_by: string | null;
  name: string | null;
  icon: string | null;
  original_name: string | null;
}

export interface HAArea {
  area_id: string;
  name: string;
  picture: string | null;
}

export interface HAState {
  entity_id: string;
  state: string;
  attributes: Record<string, any>;
  last_changed: string;
  last_updated: string;
  context: {
    id: string;
    parent_id: string | null;
    user_id: string | null;
  };
}

// ---- Aggregated Types (our API output) ----

export interface DeviceEntity {
  entity_id: string;
  state: string;
  attributes: Record<string, any>;
  last_changed: string;
  domain: string; // extracted from entity_id: "light", "switch", etc.
}

export interface AggregatedDevice {
  id: string;
  name: string;
  manufacturer: string | null;
  model: string | null;
  sw_version: string | null;
  hw_version: string | null;
  area_id: string | null;
  area_name: string | null;
  connections: { type: string; value: string }[];
  via_device_id: string | null;
  entities: DeviceEntity[];
  status: "online" | "offline" | "unknown";
  primary_entity: string | null; // main entity_id for control
  device_type: string; // "light" | "switch" | "climate" | "camera" | "sensor" | "binary_sensor" | "other"
  is_new: boolean;
}

export interface Area {
  area_id: string;
  name: string;
  device_count: number;
}
```

- [ ] **Step 2: Create HA WebSocket client**

`api/src/ha-client.ts`:
```typescript
import {
  createLongLivedTokenAuth,
  createConnection,
  subscribeEntities,
  callService,
  type Connection,
  type HassEntities,
} from "home-assistant-js-websocket";
import type { HADevice, HAEntity, HAArea, HAState } from "./types";

let connection: Connection | null = null;
let entities: HassEntities = {};

export async function connectToHA(): Promise<Connection> {
  const url = process.env.HA_URL || "http://localhost:8123";
  const token = process.env.HA_TOKEN;

  if (!token) {
    throw new Error("HA_TOKEN environment variable is required");
  }

  console.log(`Connecting to Home Assistant at ${url}...`);
  const auth = createLongLivedTokenAuth(url, token);

  connection = await createConnection({ auth });

  connection.addEventListener("ready", () => {
    console.log("HA WebSocket: connected and ready");
  });

  connection.addEventListener("disconnected", () => {
    console.log("HA WebSocket: disconnected (will auto-reconnect)");
  });

  connection.addEventListener("reconnect-error", () => {
    console.log("HA WebSocket: reconnect error");
  });

  // Subscribe to entity state changes — keeps `entities` updated in real-time
  subscribeEntities(connection, (newEntities) => {
    entities = newEntities;
  });

  console.log("HA WebSocket: authenticated and subscribed to entities");
  return connection;
}

export function getConnection(): Connection {
  if (!connection) {
    throw new Error("Not connected to Home Assistant. Call connectToHA() first.");
  }
  return connection;
}

export function getEntities(): HassEntities {
  return entities;
}

export async function fetchDeviceRegistry(): Promise<HADevice[]> {
  const conn = getConnection();
  return conn.sendMessagePromise({ type: "config/device_registry/list" });
}

export async function fetchEntityRegistry(): Promise<HAEntity[]> {
  const conn = getConnection();
  return conn.sendMessagePromise({ type: "config/entity_registry/list" });
}

export async function fetchAreaRegistry(): Promise<HAArea[]> {
  const conn = getConnection();
  return conn.sendMessagePromise({ type: "config/area_registry/list" });
}

export async function callHAService(
  domain: string,
  service: string,
  serviceData?: Record<string, any>,
  target?: { entity_id?: string | string[]; area_id?: string | string[] }
): Promise<any> {
  const conn = getConnection();
  return callService(conn, domain, service, serviceData, target);
}

export function getHAUrl(): string {
  return process.env.HA_URL || "http://localhost:8123";
}

export function getHAToken(): string {
  return process.env.HA_TOKEN || "";
}
```

- [ ] **Step 3: Wire HA client into Elysia startup**

Update `api/src/index.ts`:
```typescript
import { Elysia } from "elysia";
import { connectToHA } from "./ha-client";

const app = new Elysia()
  .get("/api/health", () => ({ status: "ok" }))
  .listen(Number(process.env.API_PORT) || 3001);

console.log(`API running on port ${app.server?.port}`);

// Connect to HA after server starts
connectToHA()
  .then(() => console.log("HA connection established"))
  .catch((err) => {
    console.error("Failed to connect to HA:", err.message);
    console.error("Make sure HA is running and HA_TOKEN is set in .env");
  });
```

- [ ] **Step 4: Commit**

```bash
git add api/src/types.ts api/src/ha-client.ts api/src/index.ts
git commit -m "feat: add HA WebSocket client with auth and entity subscription"
```

### Task 3: Device Aggregation Service

**Covers:** P3 (Device Aggregation Service), P4 (Real-Time State Updates), P11 (New Device Notifications)

**Files:**
- Create: `api/src/device-aggregator.ts`

- [ ] **Step 1: Create device aggregator**

`api/src/device-aggregator.ts`:
```typescript
import {
  fetchDeviceRegistry,
  fetchEntityRegistry,
  fetchAreaRegistry,
  getEntities,
} from "./ha-client";
import type {
  HADevice,
  HAEntity,
  HAArea,
  AggregatedDevice,
  DeviceEntity,
  Area,
} from "./types";

let previousDeviceIds: Set<string> = new Set();
let newDeviceIds: Set<string> = new Set();
let newDeviceTimestamps: Map<string, number> = new Map();

const NEW_DEVICE_TTL_MS = 5 * 60 * 1000; // Show "NEW" badge for 5 minutes

function getDomain(entityId: string): string {
  return entityId.split(".")[0];
}

function determineDeviceType(entityDomains: string[]): string {
  // Priority order for determining the "primary" type
  const priority = ["camera", "climate", "light", "switch", "sensor", "binary_sensor"];
  for (const domain of priority) {
    if (entityDomains.includes(domain)) return domain;
  }
  return entityDomains[0] || "other";
}

function determineStatus(deviceEntities: DeviceEntity[]): "online" | "offline" | "unknown" {
  if (deviceEntities.length === 0) return "unknown";

  const allUnavailable = deviceEntities.every((e) => e.state === "unavailable");
  if (allUnavailable) return "offline";

  const allUnknown = deviceEntities.every(
    (e) => e.state === "unknown" || e.state === "unavailable"
  );
  if (allUnknown) return "unknown";

  return "online";
}

export async function getAggregatedDevices(): Promise<AggregatedDevice[]> {
  const [devices, entityRegistry, areas] = await Promise.all([
    fetchDeviceRegistry(),
    fetchEntityRegistry(),
    fetchAreaRegistry(),
  ]);

  const entities = getEntities();
  const areaMap = new Map(areas.map((a) => [a.area_id, a.name]));

  // Group entity registry entries by device_id
  const entitiesByDevice = new Map<string, HAEntity[]>();
  for (const entity of entityRegistry) {
    if (entity.device_id && !entity.disabled_by && !entity.hidden_by) {
      const list = entitiesByDevice.get(entity.device_id) || [];
      list.push(entity);
      entitiesByDevice.set(entity.device_id, list);
    }
  }

  // Detect new devices
  const currentDeviceIds = new Set(devices.map((d) => d.id));
  const now = Date.now();

  if (previousDeviceIds.size > 0) {
    for (const id of currentDeviceIds) {
      if (!previousDeviceIds.has(id)) {
        newDeviceIds.add(id);
        newDeviceTimestamps.set(id, now);
      }
    }
  }
  previousDeviceIds = currentDeviceIds;

  // Clean up expired "new" badges
  for (const [id, timestamp] of newDeviceTimestamps) {
    if (now - timestamp > NEW_DEVICE_TTL_MS) {
      newDeviceIds.delete(id);
      newDeviceTimestamps.delete(id);
    }
  }

  // Build aggregated devices
  const aggregated: AggregatedDevice[] = [];

  for (const device of devices) {
    if (device.disabled_by) continue;

    const deviceEntities = entitiesByDevice.get(device.id) || [];
    const resolvedEntities: DeviceEntity[] = [];
    const domains: string[] = [];

    for (const regEntity of deviceEntities) {
      const stateObj = entities[regEntity.entity_id];
      const domain = getDomain(regEntity.entity_id);
      domains.push(domain);

      resolvedEntities.push({
        entity_id: regEntity.entity_id,
        state: stateObj?.state ?? "unknown",
        attributes: stateObj?.attributes ?? {},
        last_changed: stateObj?.last_changed ?? "",
        domain,
      });
    }

    // Resolve area: entity area_id overrides device area_id
    let areaId = device.area_id;
    for (const regEntity of deviceEntities) {
      if (regEntity.area_id) {
        areaId = regEntity.area_id;
        break; // Use first entity override found
      }
    }

    const deviceType = determineDeviceType([...new Set(domains)]);
    const primaryEntity = resolvedEntities.find((e) => e.domain === deviceType)?.entity_id ?? null;

    aggregated.push({
      id: device.id,
      name: device.name_by_user || device.name || "Unknown Device",
      manufacturer: device.manufacturer,
      model: device.model,
      sw_version: device.sw_version,
      hw_version: device.hw_version,
      area_id: areaId,
      area_name: areaId ? areaMap.get(areaId) ?? null : null,
      connections: device.connections.map(([type, value]) => ({ type, value })),
      via_device_id: device.via_device_id,
      entities: resolvedEntities,
      status: determineStatus(resolvedEntities),
      primary_entity: primaryEntity,
      device_type: deviceType,
      is_new: newDeviceIds.has(device.id),
    });
  }

  return aggregated;
}

export async function getAreas(): Promise<Area[]> {
  const [areas, devices, entityRegistry] = await Promise.all([
    fetchAreaRegistry(),
    fetchDeviceRegistry(),
    fetchEntityRegistry(),
  ]);

  // Count devices per area (respecting entity area overrides)
  const deviceAreaMap = new Map<string, string | null>();
  for (const device of devices) {
    if (!device.disabled_by) {
      deviceAreaMap.set(device.id, device.area_id);
    }
  }

  // Apply entity area overrides
  for (const entity of entityRegistry) {
    if (entity.device_id && entity.area_id && !entity.disabled_by) {
      deviceAreaMap.set(entity.device_id, entity.area_id);
    }
  }

  const countByArea = new Map<string, number>();
  for (const areaId of deviceAreaMap.values()) {
    if (areaId) {
      countByArea.set(areaId, (countByArea.get(areaId) || 0) + 1);
    }
  }

  return areas.map((a) => ({
    area_id: a.area_id,
    name: a.name,
    device_count: countByArea.get(a.area_id) || 0,
  }));
}

export function getNewDeviceNames(allDevices: AggregatedDevice[]): string[] {
  return allDevices.filter((d) => d.is_new).map((d) => d.name);
}
```

- [ ] **Step 2: Commit**

```bash
git add api/src/device-aggregator.ts
git commit -m "feat: add device aggregation service combining registries + states"
```

### Task 4: REST API Endpoints

**Covers:** P5 (REST API Endpoints for Dashboard)

**Files:**
- Create: `api/src/routes/devices.ts`
- Create: `api/src/routes/areas.ts`
- Create: `api/src/routes/services.ts`
- Create: `api/src/routes/camera.ts`
- Modify: `api/src/index.ts`

- [ ] **Step 1: Create device routes**

`api/src/routes/devices.ts`:
```typescript
import { Elysia } from "elysia";
import { getAggregatedDevices, getNewDeviceNames } from "../device-aggregator";

export const deviceRoutes = new Elysia()
  .get("/api/devices", async () => {
    try {
      const devices = await getAggregatedDevices();
      const newDevices = getNewDeviceNames(devices);
      return {
        devices,
        new_devices: newDevices,
        count: devices.length,
      };
    } catch (error: any) {
      return new Response(
        JSON.stringify({ error: "Failed to fetch devices", message: error.message }),
        { status: 502, headers: { "Content-Type": "application/json" } }
      );
    }
  })
  .get("/api/devices/:id", async ({ params }) => {
    try {
      const devices = await getAggregatedDevices();
      const device = devices.find((d) => d.id === params.id);
      if (!device) {
        return new Response(
          JSON.stringify({ error: "Device not found" }),
          { status: 404, headers: { "Content-Type": "application/json" } }
        );
      }
      return device;
    } catch (error: any) {
      return new Response(
        JSON.stringify({ error: "Failed to fetch device", message: error.message }),
        { status: 502, headers: { "Content-Type": "application/json" } }
      );
    }
  });
```

- [ ] **Step 2: Create area routes**

`api/src/routes/areas.ts`:
```typescript
import { Elysia } from "elysia";
import { getAreas } from "../device-aggregator";

export const areaRoutes = new Elysia()
  .get("/api/areas", async () => {
    try {
      const areas = await getAreas();
      return { areas };
    } catch (error: any) {
      return new Response(
        JSON.stringify({ error: "Failed to fetch areas", message: error.message }),
        { status: 502, headers: { "Content-Type": "application/json" } }
      );
    }
  });
```

- [ ] **Step 3: Create service call proxy**

`api/src/routes/services.ts`:
```typescript
import { Elysia, t } from "elysia";
import { callHAService } from "../ha-client";

export const serviceRoutes = new Elysia()
  .post("/api/services/:domain/:service", async ({ params, body }) => {
    try {
      const { domain, service } = params;
      const { entity_id, area_id, ...serviceData } = body as any;

      const target: Record<string, any> = {};
      if (entity_id) target.entity_id = entity_id;
      if (area_id) target.area_id = area_id;

      await callHAService(domain, service, serviceData, target);

      return { success: true, domain, service, target };
    } catch (error: any) {
      return new Response(
        JSON.stringify({ error: "Service call failed", message: error.message }),
        { status: 502, headers: { "Content-Type": "application/json" } }
      );
    }
  });
```

- [ ] **Step 4: Create camera snapshot proxy**

`api/src/routes/camera.ts`:
```typescript
import { Elysia } from "elysia";
import { getHAUrl, getHAToken } from "../ha-client";

export const cameraRoutes = new Elysia()
  .get("/api/camera/:entity_id/snapshot", async ({ params }) => {
    try {
      const { entity_id } = params;
      const haUrl = getHAUrl();
      const token = getHAToken();
      const timestamp = Date.now();

      const response = await fetch(
        `${haUrl}/api/camera_proxy/${entity_id}?time=${timestamp}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      if (!response.ok) {
        return new Response(
          JSON.stringify({ error: "Camera snapshot failed", status: response.status }),
          { status: response.status, headers: { "Content-Type": "application/json" } }
        );
      }

      const imageBuffer = await response.arrayBuffer();
      return new Response(imageBuffer, {
        headers: {
          "Content-Type": response.headers.get("Content-Type") || "image/jpeg",
          "Cache-Control": "no-cache",
        },
      });
    } catch (error: any) {
      return new Response(
        JSON.stringify({ error: "Camera proxy failed", message: error.message }),
        { status: 502, headers: { "Content-Type": "application/json" } }
      );
    }
  });
```

- [ ] **Step 5: Wire all routes into Elysia app**

Update `api/src/index.ts`:
```typescript
import { Elysia } from "elysia";
import { connectToHA } from "./ha-client";
import { deviceRoutes } from "./routes/devices";
import { areaRoutes } from "./routes/areas";
import { serviceRoutes } from "./routes/services";
import { cameraRoutes } from "./routes/camera";

const app = new Elysia()
  .get("/api/health", () => ({ status: "ok" }))
  .use(deviceRoutes)
  .use(areaRoutes)
  .use(serviceRoutes)
  .use(cameraRoutes)
  .listen(Number(process.env.API_PORT) || 3001);

console.log(`API running on port ${app.server?.port}`);

connectToHA()
  .then(() => console.log("HA connection established"))
  .catch((err) => {
    console.error("Failed to connect to HA:", err.message);
    console.error("Make sure HA is running and HA_TOKEN is set in .env");
  });
```

- [ ] **Step 6: Commit**

```bash
git add api/src/routes/ api/src/index.ts
git commit -m "feat: add REST API endpoints for devices, areas, services, and camera"
```

---

## Phase C: Frontend Core (P6, P9)

### Task 5: API Client and Types

**Covers:** Frontend data fetching foundation

**Files:**
- Create: `dashboard/src/types.ts`
- Create: `dashboard/src/api.ts`
- Create: `dashboard/src/hooks/useDevices.ts`
- Create: `dashboard/src/hooks/useAreas.ts`

- [ ] **Step 1: Create frontend types**

`dashboard/src/types.ts`:
```typescript
export interface DeviceEntity {
  entity_id: string;
  state: string;
  attributes: Record<string, any>;
  last_changed: string;
  domain: string;
}

export interface Device {
  id: string;
  name: string;
  manufacturer: string | null;
  model: string | null;
  sw_version: string | null;
  hw_version: string | null;
  area_id: string | null;
  area_name: string | null;
  connections: { type: string; value: string }[];
  via_device_id: string | null;
  entities: DeviceEntity[];
  status: "online" | "offline" | "unknown";
  primary_entity: string | null;
  device_type: string;
  is_new: boolean;
}

export interface Area {
  area_id: string;
  name: string;
  device_count: number;
}

export interface DevicesResponse {
  devices: Device[];
  new_devices: string[];
  count: number;
}

export interface AreasResponse {
  areas: Area[];
}
```

- [ ] **Step 2: Create API client**

`dashboard/src/api.ts`:
```typescript
import type { DevicesResponse, AreasResponse } from "./types";

const API_BASE = "/api";

export async function fetchDevices(): Promise<DevicesResponse> {
  const res = await fetch(`${API_BASE}/devices`);
  if (!res.ok) throw new Error(`Failed to fetch devices: ${res.status}`);
  return res.json();
}

export async function fetchAreas(): Promise<AreasResponse> {
  const res = await fetch(`${API_BASE}/areas`);
  if (!res.ok) throw new Error(`Failed to fetch areas: ${res.status}`);
  return res.json();
}

export async function callService(
  domain: string,
  service: string,
  data: Record<string, any> = {}
): Promise<void> {
  const res = await fetch(`${API_BASE}/services/${domain}/${service}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(`Service call failed: ${res.status}`);
}

export function cameraSnapshotUrl(entityId: string): string {
  return `${API_BASE}/camera/${entityId}/snapshot?t=${Date.now()}`;
}
```

- [ ] **Step 3: Create useDevices hook**

`dashboard/src/hooks/useDevices.ts`:
```typescript
import { useState, useEffect, useCallback } from "react";
import { fetchDevices } from "../api";
import type { Device } from "../types";

const POLL_INTERVAL_MS = 10_000;

export function useDevices() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [newDeviceNames, setNewDeviceNames] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const data = await fetchDevices();
      setDevices(data.devices);
      setNewDeviceNames(data.new_devices);
      setError(null);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [refresh]);

  return { devices, newDeviceNames, loading, error, refresh };
}
```

- [ ] **Step 4: Create useAreas hook**

`dashboard/src/hooks/useAreas.ts`:
```typescript
import { useState, useEffect } from "react";
import { fetchAreas } from "../api";
import type { Area } from "../types";

export function useAreas() {
  const [areas, setAreas] = useState<Area[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAreas()
      .then((data) => setAreas(data.areas))
      .catch(() => {}) // Areas are non-critical
      .finally(() => setLoading(false));
  }, []);

  return { areas, loading };
}
```

- [ ] **Step 5: Commit**

```bash
git add dashboard/src/types.ts dashboard/src/api.ts dashboard/src/hooks/
git commit -m "feat: add frontend API client, types, and polling hooks"
```

### Task 6: Device Card Grid and Area Grouping

**Covers:** P6 (Device Card Grid), P9 (Room/Area Grouping)

**Files:**
- Create: `dashboard/src/components/StatusBadge.tsx`
- Create: `dashboard/src/components/DeviceCard.tsx`
- Create: `dashboard/src/components/AreaFilter.tsx`
- Create: `dashboard/src/components/DeviceGrid.tsx`
- Create: `dashboard/src/components/NotificationToast.tsx`
- Modify: `dashboard/src/App.tsx`

- [ ] **Step 1: Create StatusBadge component**

`dashboard/src/components/StatusBadge.tsx`:
```tsx
interface StatusBadgeProps {
  status: "online" | "offline" | "unknown";
}

const statusConfig = {
  online: { label: "Online", color: "bg-emerald-500" },
  offline: { label: "Offline", color: "bg-red-500" },
  unknown: { label: "Unknown", color: "bg-yellow-500" },
};

export default function StatusBadge({ status }: StatusBadgeProps) {
  const config = statusConfig[status];
  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium text-white ${config.color}`}>
      <span className={`w-1.5 h-1.5 rounded-full bg-white/60`} />
      {config.label}
    </span>
  );
}
```

- [ ] **Step 2: Create DeviceCard component**

`dashboard/src/components/DeviceCard.tsx`:
```tsx
import type { Device } from "../types";
import StatusBadge from "./StatusBadge";

const deviceIcons: Record<string, string> = {
  light: "\u{1F4A1}",
  switch: "\u{1F50C}",
  climate: "\u{1F321}\u{FE0F}",
  camera: "\u{1F4F7}",
  sensor: "\u{1F4CA}",
  binary_sensor: "\u{1F6A8}",
  other: "\u{1F4E6}",
};

interface DeviceCardProps {
  device: Device;
  children?: React.ReactNode; // Slot for device-specific controls
}

export default function DeviceCard({ device, children }: DeviceCardProps) {
  const icon = deviceIcons[device.device_type] || deviceIcons.other;
  const mac = device.connections.find((c) => c.type === "mac")?.value;
  const ip = device.connections.find((c) => c.type === "ip")?.value;

  return (
    <div className={`bg-gray-900 border border-gray-800 rounded-xl p-4 flex flex-col gap-3 relative ${device.is_new ? "ring-2 ring-blue-500" : ""}`}>
      {device.is_new && (
        <span className="absolute -top-2 -right-2 bg-blue-500 text-white text-xs font-bold px-2 py-0.5 rounded-full">
          NEW
        </span>
      )}

      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-2xl flex-shrink-0">{icon}</span>
          <div className="min-w-0">
            <h3 className="text-sm font-semibold text-white truncate">{device.name}</h3>
            {device.manufacturer && (
              <p className="text-xs text-gray-400 truncate">
                {device.manufacturer}{device.model ? ` ${device.model}` : ""}
              </p>
            )}
          </div>
        </div>
        <StatusBadge status={device.status} />
      </div>

      {(mac || ip) && (
        <div className="text-xs text-gray-500 font-mono">
          {mac && <div>MAC: {mac}</div>}
          {ip && <div>IP: {ip}</div>}
        </div>
      )}

      {children}
    </div>
  );
}
```

- [ ] **Step 3: Create AreaFilter component**

`dashboard/src/components/AreaFilter.tsx`:
```tsx
import type { Area } from "../types";

interface AreaFilterProps {
  areas: Area[];
  selectedArea: string | null;
  totalDevices: number;
  unassignedCount: number;
  onSelect: (areaId: string | null) => void;
}

export default function AreaFilter({
  areas,
  selectedArea,
  totalDevices,
  unassignedCount,
  onSelect,
}: AreaFilterProps) {
  return (
    <div className="flex gap-2 flex-wrap">
      <button
        onClick={() => onSelect(null)}
        className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
          selectedArea === null
            ? "bg-blue-600 text-white"
            : "bg-gray-800 text-gray-300 hover:bg-gray-700"
        }`}
      >
        All ({totalDevices})
      </button>
      {areas.map((area) => (
        <button
          key={area.area_id}
          onClick={() => onSelect(area.area_id)}
          className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
            selectedArea === area.area_id
              ? "bg-blue-600 text-white"
              : "bg-gray-800 text-gray-300 hover:bg-gray-700"
          }`}
        >
          {area.name} ({area.device_count})
        </button>
      ))}
      {unassignedCount > 0 && (
        <button
          onClick={() => onSelect("__unassigned__")}
          className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
            selectedArea === "__unassigned__"
              ? "bg-blue-600 text-white"
              : "bg-gray-800 text-gray-300 hover:bg-gray-700"
          }`}
        >
          Unassigned ({unassignedCount})
        </button>
      )}
    </div>
  );
}
```

- [ ] **Step 4: Create DeviceGrid component**

`dashboard/src/components/DeviceGrid.tsx`:
```tsx
import type { Device, Area } from "../types";
import DeviceCard from "./DeviceCard";
import LightCard from "./LightCard";
import SwitchCard from "./SwitchCard";
import ClimateCard from "./ClimateCard";
import CameraCard from "./CameraCard";
import SensorCard from "./SensorCard";

interface DeviceGridProps {
  devices: Device[];
  areas: Area[];
  selectedArea: string | null;
}

function renderDeviceControls(device: Device) {
  switch (device.device_type) {
    case "light":
      return <LightCard device={device} />;
    case "switch":
      return <SwitchCard device={device} />;
    case "climate":
      return <ClimateCard device={device} />;
    case "camera":
      return <CameraCard device={device} />;
    case "sensor":
    case "binary_sensor":
      return <SensorCard device={device} />;
    default:
      return null;
  }
}

export default function DeviceGrid({ devices, areas, selectedArea }: DeviceGridProps) {
  // Filter by selected area
  let filtered = devices;
  if (selectedArea === "__unassigned__") {
    filtered = devices.filter((d) => !d.area_id);
  } else if (selectedArea) {
    filtered = devices.filter((d) => d.area_id === selectedArea);
  }

  // Group by area
  const grouped = new Map<string, Device[]>();
  for (const device of filtered) {
    const key = device.area_name || "Unassigned";
    const list = grouped.get(key) || [];
    list.push(device);
    grouped.set(key, list);
  }

  // Sort: named areas first (alphabetically), "Unassigned" last
  const sortedGroups = [...grouped.entries()].sort(([a], [b]) => {
    if (a === "Unassigned") return 1;
    if (b === "Unassigned") return -1;
    return a.localeCompare(b);
  });

  if (filtered.length === 0) {
    return (
      <div className="text-center text-gray-500 py-12">
        No devices found.
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {sortedGroups.map(([areaName, areaDevices]) => (
        <section key={areaName}>
          {/* Only show section headers when not filtering by a specific area */}
          {!selectedArea && (
            <h2 className="text-lg font-semibold text-gray-300 mb-3">
              {areaName}
              <span className="text-sm text-gray-500 ml-2">({areaDevices.length})</span>
            </h2>
          )}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {areaDevices.map((device) => (
              <DeviceCard key={device.id} device={device}>
                {renderDeviceControls(device)}
              </DeviceCard>
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}
```

- [ ] **Step 5: Create NotificationToast component**

`dashboard/src/components/NotificationToast.tsx`:
```tsx
import { useState, useEffect } from "react";

interface NotificationToastProps {
  deviceNames: string[];
}

export default function NotificationToast({ deviceNames }: NotificationToastProps) {
  const [visible, setVisible] = useState(false);
  const [displayedNames, setDisplayedNames] = useState<string[]>([]);

  useEffect(() => {
    if (deviceNames.length > 0 && deviceNames.join(",") !== displayedNames.join(",")) {
      setDisplayedNames(deviceNames);
      setVisible(true);
      const timer = setTimeout(() => setVisible(false), 10_000);
      return () => clearTimeout(timer);
    }
  }, [deviceNames, displayedNames]);

  if (!visible || displayedNames.length === 0) return null;

  return (
    <div className="fixed top-4 right-4 z-50 bg-blue-600 text-white px-4 py-3 rounded-lg shadow-lg max-w-sm">
      <div className="flex items-center justify-between gap-2">
        <div>
          <p className="text-sm font-semibold">New device discovered!</p>
          {displayedNames.map((name) => (
            <p key={name} className="text-sm text-blue-100">{name}</p>
          ))}
        </div>
        <button onClick={() => setVisible(false)} className="text-blue-200 hover:text-white">
          X
        </button>
      </div>
    </div>
  );
}
```

- [ ] **Step 6: Note — control components created in next task**

The `DeviceGrid` imports `LightCard`, `SwitchCard`, `ClimateCard`, `CameraCard`, and `SensorCard`. These are created in Tasks 7-8. For now, create empty placeholder files so TypeScript doesn't error:

Create placeholder files (these will be replaced in the next tasks):

`dashboard/src/components/LightCard.tsx`:
```tsx
import type { Device } from "../types";
export default function LightCard({ device }: { device: Device }) {
  return null;
}
```

`dashboard/src/components/SwitchCard.tsx`:
```tsx
import type { Device } from "../types";
export default function SwitchCard({ device }: { device: Device }) {
  return null;
}
```

`dashboard/src/components/ClimateCard.tsx`:
```tsx
import type { Device } from "../types";
export default function ClimateCard({ device }: { device: Device }) {
  return null;
}
```

`dashboard/src/components/CameraCard.tsx`:
```tsx
import type { Device } from "../types";
export default function CameraCard({ device }: { device: Device }) {
  return null;
}
```

`dashboard/src/components/SensorCard.tsx`:
```tsx
import type { Device } from "../types";
export default function SensorCard({ device }: { device: Device }) {
  return null;
}
```

- [ ] **Step 7: Update App.tsx with layout, hooks, and grid**

`dashboard/src/App.tsx`:
```tsx
import { useState } from "react";
import { useDevices } from "./hooks/useDevices";
import { useAreas } from "./hooks/useAreas";
import AreaFilter from "./components/AreaFilter";
import DeviceGrid from "./components/DeviceGrid";
import NotificationToast from "./components/NotificationToast";

export default function App() {
  const { devices, newDeviceNames, loading, error } = useDevices();
  const { areas } = useAreas();
  const [selectedArea, setSelectedArea] = useState<string | null>(null);

  const unassignedCount = devices.filter((d) => !d.area_id).length;

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <NotificationToast deviceNames={newDeviceNames} />

      <header className="border-b border-gray-800 px-6 py-4">
        <h1 className="text-2xl font-bold">SmartHub</h1>
        <p className="text-sm text-gray-400">
          {loading ? "Loading devices..." : `${devices.length} devices`}
          {error && <span className="text-red-400 ml-2">Error: {error}</span>}
        </p>
      </header>

      <main className="px-6 py-4 space-y-4">
        <AreaFilter
          areas={areas}
          selectedArea={selectedArea}
          totalDevices={devices.length}
          unassignedCount={unassignedCount}
          onSelect={setSelectedArea}
        />

        <DeviceGrid
          devices={devices}
          areas={areas}
          selectedArea={selectedArea}
        />
      </main>
    </div>
  );
}
```

- [ ] **Step 8: Commit**

```bash
git add dashboard/src/
git commit -m "feat: add device card grid with area grouping and notifications"
```

---

## Phase D: Device Controls (P7, P8, P10)

### Task 7: Light, Switch, and Climate Controls

**Covers:** P7 (Device Control — Lights, Switches, Thermostat)

**Files:**
- Modify: `dashboard/src/components/LightCard.tsx`
- Modify: `dashboard/src/components/SwitchCard.tsx`
- Modify: `dashboard/src/components/ClimateCard.tsx`

- [ ] **Step 1: Implement LightCard**

`dashboard/src/components/LightCard.tsx`:
```tsx
import { useState } from "react";
import type { Device } from "../types";
import { callService } from "../api";

export default function LightCard({ device }: { device: Device }) {
  const entity = device.entities.find((e) => e.domain === "light");
  if (!entity) return null;

  // Optimistic state: tracks local toggle/brightness until next poll confirms
  const [optimisticOn, setOptimisticOn] = useState<boolean | null>(null);
  const [optimisticBrightness, setOptimisticBrightness] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);

  const isOn = optimisticOn ?? entity.state === "on";
  const brightness = optimisticBrightness ?? entity.attributes.brightness ?? 0;
  const brightnessPercent = Math.round((brightness / 255) * 100);

  async function toggle() {
    setLoading(true);
    setOptimisticOn(!isOn); // Optimistic update
    try {
      await callService("light", isOn ? "turn_off" : "turn_on", {
        entity_id: entity.entity_id,
      });
    } finally {
      setLoading(false);
      // Reset optimistic state after a short delay to let poll catch up
      setTimeout(() => setOptimisticOn(null), 2000);
    }
  }

  async function setBrightness(value: number) {
    const rawBrightness = Math.round((value / 100) * 255);
    setOptimisticBrightness(rawBrightness); // Optimistic update
    await callService("light", "turn_on", {
      entity_id: entity.entity_id,
      brightness: rawBrightness,
    });
    setTimeout(() => setOptimisticBrightness(null), 2000);
  }

  return (
    <div className="space-y-2 pt-2 border-t border-gray-800">
      <div className="flex items-center justify-between">
        <span className="text-xs text-gray-400">
          {isOn ? `On (${brightnessPercent}%)` : "Off"}
        </span>
        <button
          onClick={toggle}
          disabled={loading || device.status === "offline"}
          className={`relative w-10 h-5 rounded-full transition-colors ${
            isOn ? "bg-blue-500" : "bg-gray-700"
          } ${loading ? "opacity-50" : ""}`}
        >
          <span
            className={`absolute top-0.5 w-4 h-4 rounded-full bg-white transition-transform ${
              isOn ? "left-5" : "left-0.5"
            }`}
          />
        </button>
      </div>
      {isOn && (
        <input
          type="range"
          min={1}
          max={100}
          value={brightnessPercent}
          onChange={(e) => setBrightness(Number(e.target.value))}
          className="w-full h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
        />
      )}
    </div>
  );
}
```

- [ ] **Step 2: Implement SwitchCard**

`dashboard/src/components/SwitchCard.tsx`:
```tsx
import { useState } from "react";
import type { Device } from "../types";
import { callService } from "../api";

export default function SwitchCard({ device }: { device: Device }) {
  const entity = device.entities.find((e) => e.domain === "switch");
  if (!entity) return null;

  const [optimisticOn, setOptimisticOn] = useState<boolean | null>(null);
  const [loading, setLoading] = useState(false);

  const isOn = optimisticOn ?? entity.state === "on";

  async function toggle() {
    setLoading(true);
    setOptimisticOn(!isOn); // Optimistic update
    try {
      await callService("switch", "toggle", {
        entity_id: entity.entity_id,
      });
    } finally {
      setLoading(false);
      setTimeout(() => setOptimisticOn(null), 2000);
    }
  }

  return (
    <div className="pt-2 border-t border-gray-800">
      <div className="flex items-center justify-between">
        <span className="text-xs text-gray-400">{isOn ? "On" : "Off"}</span>
        <button
          onClick={toggle}
          disabled={loading || device.status === "offline"}
          className={`relative w-10 h-5 rounded-full transition-colors ${
            isOn ? "bg-blue-500" : "bg-gray-700"
          } ${loading ? "opacity-50" : ""}`}
        >
          <span
            className={`absolute top-0.5 w-4 h-4 rounded-full bg-white transition-transform ${
              isOn ? "left-5" : "left-0.5"
            }`}
          />
        </button>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Implement ClimateCard**

`dashboard/src/components/ClimateCard.tsx`:
```tsx
import { useState } from "react";
import type { Device } from "../types";
import { callService } from "../api";

export default function ClimateCard({ device }: { device: Device }) {
  const entity = device.entities.find((e) => e.domain === "climate");
  if (!entity) return null;

  const currentTemp = entity.attributes.current_temperature;
  const targetTemp = entity.attributes.temperature;
  const hvacMode = entity.state;
  const hvacModes: string[] = entity.attributes.hvac_modes || [];
  const minTemp = entity.attributes.min_temp ?? 16;
  const maxTemp = entity.attributes.max_temp ?? 30;
  const unit = entity.attributes.temperature_unit || "\u00B0C";

  const [loading, setLoading] = useState(false);

  async function setTemp(delta: number) {
    if (targetTemp == null) return;
    const newTemp = Math.min(maxTemp, Math.max(minTemp, targetTemp + delta));
    setLoading(true);
    try {
      await callService("climate", "set_temperature", {
        entity_id: entity.entity_id,
        temperature: newTemp,
      });
    } finally {
      setLoading(false);
    }
  }

  async function setMode(mode: string) {
    setLoading(true);
    try {
      await callService("climate", "set_hvac_mode", {
        entity_id: entity.entity_id,
        hvac_mode: mode,
      });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-2 pt-2 border-t border-gray-800">
      <div className="flex items-center justify-between text-sm">
        <span className="text-gray-400">
          Current: {currentTemp != null ? `${currentTemp}${unit}` : "--"}
        </span>
        <span className="text-white font-medium">
          Target: {targetTemp != null ? `${targetTemp}${unit}` : "--"}
        </span>
      </div>

      <div className="flex items-center justify-center gap-3">
        <button
          onClick={() => setTemp(-0.5)}
          disabled={loading || device.status === "offline"}
          className="w-8 h-8 rounded-full bg-gray-800 text-white hover:bg-gray-700 disabled:opacity-50 text-lg"
        >
          -
        </button>
        <span className="text-lg font-bold text-white w-16 text-center">
          {targetTemp != null ? `${targetTemp}${unit}` : "--"}
        </span>
        <button
          onClick={() => setTemp(0.5)}
          disabled={loading || device.status === "offline"}
          className="w-8 h-8 rounded-full bg-gray-800 text-white hover:bg-gray-700 disabled:opacity-50 text-lg"
        >
          +
        </button>
      </div>

      {hvacModes.length > 0 && (
        <div className="flex gap-1 flex-wrap">
          {hvacModes.map((mode) => (
            <button
              key={mode}
              onClick={() => setMode(mode)}
              disabled={loading || device.status === "offline"}
              className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
                hvacMode === mode
                  ? "bg-blue-600 text-white"
                  : "bg-gray-800 text-gray-400 hover:bg-gray-700"
              }`}
            >
              {mode}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 4: Commit**

```bash
git add dashboard/src/components/LightCard.tsx dashboard/src/components/SwitchCard.tsx dashboard/src/components/ClimateCard.tsx
git commit -m "feat: add light, switch, and climate device controls"
```

### Task 8: Camera and Sensor Cards

**Covers:** P8 (Camera Feed Display), P10 (Sensor Readings Display)

**Files:**
- Modify: `dashboard/src/components/CameraCard.tsx`
- Modify: `dashboard/src/components/SensorCard.tsx`

- [ ] **Step 1: Implement CameraCard**

`dashboard/src/components/CameraCard.tsx`:
```tsx
import { useState, useEffect } from "react";
import type { Device } from "../types";
import { cameraSnapshotUrl } from "../api";

export default function CameraCard({ device }: { device: Device }) {
  const entity = device.entities.find((e) => e.domain === "camera");
  if (!entity) return null;

  const [enlarged, setEnlarged] = useState(false);
  const [imgKey, setImgKey] = useState(Date.now());

  // Refresh snapshot every 10 seconds
  useEffect(() => {
    const interval = setInterval(() => setImgKey(Date.now()), 10_000);
    return () => clearInterval(interval);
  }, []);

  const snapshotUrl = cameraSnapshotUrl(entity.entity_id) + `&k=${imgKey}`;

  return (
    <>
      <div
        className="pt-2 border-t border-gray-800 cursor-pointer"
        onClick={() => setEnlarged(true)}
      >
        <img
          src={snapshotUrl}
          alt={device.name}
          className="w-full h-32 object-cover rounded-lg bg-gray-800"
          onError={(e) => {
            (e.target as HTMLImageElement).style.display = "none";
          }}
        />
        <p className="text-xs text-gray-500 mt-1 text-center">Click to enlarge</p>
      </div>

      {enlarged && (
        <div
          className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4"
          onClick={() => setEnlarged(false)}
        >
          <div className="max-w-4xl w-full">
            <img
              src={snapshotUrl}
              alt={device.name}
              className="w-full rounded-lg"
            />
            <p className="text-center text-gray-400 mt-2">{device.name}</p>
          </div>
        </div>
      )}
    </>
  );
}
```

- [ ] **Step 2: Implement SensorCard**

`dashboard/src/components/SensorCard.tsx`:
```tsx
import type { Device } from "../types";

const sensorIcons: Record<string, string> = {
  temperature: "\u{1F321}\u{FE0F}",
  humidity: "\u{1F4A7}",
  motion: "\u{1F3C3}",
  power: "\u26A1",
  energy: "\u26A1",
  battery: "\u{1F50B}",
  illuminance: "\u2600\u{FE0F}",
  pressure: "\u{1F4CA}",
  door: "\u{1F6AA}",
  window: "\u{1FA9F}",
  occupancy: "\u{1F464}",
  default: "\u{1F4CA}",
};

const binaryLabels: Record<string, [string, string]> = {
  motion: ["Motion detected", "Clear"],
  door: ["Open", "Closed"],
  window: ["Open", "Closed"],
  occupancy: ["Occupied", "Clear"],
  smoke: ["Detected!", "Clear"],
  moisture: ["Wet", "Dry"],
};

export default function SensorCard({ device }: { device: Device }) {
  const sensors = device.entities.filter(
    (e) => e.domain === "sensor" || e.domain === "binary_sensor"
  );
  if (sensors.length === 0) return null;

  return (
    <div className="space-y-1.5 pt-2 border-t border-gray-800">
      {sensors.map((entity) => {
        const deviceClass = entity.attributes.device_class || "default";
        const icon = sensorIcons[deviceClass] || sensorIcons.default;
        const unit = entity.attributes.unit_of_measurement || "";

        if (entity.domain === "binary_sensor") {
          const labels = binaryLabels[deviceClass] || ["On", "Off"];
          const isOn = entity.state === "on";
          return (
            <div key={entity.entity_id} className="flex items-center justify-between text-sm">
              <span className="text-gray-400">
                {icon} {entity.attributes.friendly_name || deviceClass}
              </span>
              <span className={isOn ? "text-yellow-400 font-medium" : "text-gray-500"}>
                {isOn ? labels[0] : labels[1]}
              </span>
            </div>
          );
        }

        // Numeric sensor
        const value = entity.state !== "unknown" && entity.state !== "unavailable"
          ? parseFloat(entity.state)
          : null;

        return (
          <div key={entity.entity_id} className="flex items-center justify-between text-sm">
            <span className="text-gray-400">
              {icon} {entity.attributes.friendly_name || deviceClass}
            </span>
            <span className="text-white font-medium">
              {value != null ? `${Number.isInteger(value) ? value : value.toFixed(1)}${unit}` : "--"}
            </span>
          </div>
        );
      })}
    </div>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add dashboard/src/components/CameraCard.tsx dashboard/src/components/SensorCard.tsx
git commit -m "feat: add camera snapshot display and sensor reading cards"
```

---

## Phase E: Integration Verification

### Task 9: Build Verification and Final Touches

**Covers:** Verify all P1-P11 criteria are met

**Files:**
- Possibly minor fixes across all files

- [ ] **Step 1: Verify API compiles and starts**

```bash
cd /home/edgenesis/Downloads/home-assistant/api && bun run src/index.ts &
# Expected: "API running on port 3001"
# (Will log HA connection error since HA isn't running — that's OK)
curl http://localhost:3001/api/health
# Expected: {"status":"ok"}
```

- [ ] **Step 2: Verify dashboard builds successfully**

```bash
cd /home/edgenesis/Downloads/home-assistant/dashboard && npm run build
# Expected: vite build succeeds with no TypeScript errors
```

- [ ] **Step 3: Verify Docker Compose config is valid**

```bash
cd /home/edgenesis/Downloads/home-assistant && docker compose config --quiet
# Expected: no errors (validates docker-compose.yml syntax)
```

- [ ] **Step 4: Verify Docker Compose starts all services**

```bash
cd /home/edgenesis/Downloads/home-assistant && docker compose up -d
# Expected: all 3 containers start successfully
docker compose ps
# Expected: homeassistant, smarthub-api, smarthub-dashboard all show "running"
# Then clean up:
docker compose down
```

- [ ] **Step 5: Run final review of all endpoints**

Manually verify the API surface:
- `GET /api/health` — health check
- `GET /api/devices` — aggregated device list
- `GET /api/devices/:id` — single device
- `GET /api/areas` — area list
- `POST /api/services/:domain/:service` — service call proxy
- `GET /api/camera/:entity_id/snapshot` — camera proxy

- [ ] **Step 6: Final commit**

```bash
git add -A
git commit -m "feat: Phase 1 MVP complete — smart home dashboard with HA integration"
```

---

## Verification Checklist (maps to phase1-issues.md)

| Finding | Success Criteria Summary | Task |
|---------|-------------------------|------|
| P1 | Docker Compose starts 3 services, HA on :8123, API on :3001, Dashboard on :3000 | Task 1 |
| P2 | WebSocket connects, authenticates, auto-reconnects, logs state | Task 2 |
| P3 | Fetches 3 registries, produces unified list, correct offline logic, area override | Task 3 |
| P4 | Subscribes to state changes, updates within 1s, dashboard polls every 10s | Task 2-3 |
| P5 | All REST endpoints return correct data, error handling | Task 4 |
| P6 | Responsive card grid, name/manufacturer/IP/MAC/status badge, grouped by area, auto-refresh | Task 6 |
| P7 | Light toggle + brightness, switch toggle, thermostat temp + mode | Task 7 |
| P8 | Camera snapshot, 10s refresh, click to enlarge | Task 8 |
| P9 | Area tabs, "Unassigned" group, device count, entity area override | Task 6 |
| P10 | Sensor value + unit, device_class icon, binary labels, read-only | Task 8 |
| P11 | New device detection within 30s, notification toast, "NEW" badge | Task 3, 6 |
