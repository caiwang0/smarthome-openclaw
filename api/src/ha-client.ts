import {
  createLongLivedTokenAuth,
  createConnection,
  subscribeEntities,
  callService,
  type Connection,
  type HassEntities,
  type ConnectionOptions,
} from "home-assistant-js-websocket";
import type { HADevice, HAEntity, HAArea } from "./types";

let connection: Connection | null = null;
let entities: HassEntities = {};
let connectionReady = false;

// Build a createSocket function compatible with the HA JS library
// The library expects the socket factory to handle auth and return a ready socket
function createHASocket(url: string, token: string): ConnectionOptions["createSocket"] {
  const wsUrl = url.replace(/^http/, "ws") + "/api/websocket";

  return async () => {
    const ws = new WebSocket(wsUrl);

    await new Promise<void>((resolve, reject) => {
      const timeout = setTimeout(() => reject(new Error("WebSocket connection timeout")), 10000);

      ws.addEventListener("message", function handler(event: MessageEvent) {
        const data = JSON.parse(String(event.data));

        if (data.type === "auth_required") {
          ws.send(JSON.stringify({ type: "auth", access_token: token }));
        } else if (data.type === "auth_ok") {
          clearTimeout(timeout);
          // Attach ha_version so the library can read it
          (ws as any).haVersion = data.ha_version;
          ws.removeEventListener("message", handler);
          resolve();
        } else if (data.type === "auth_invalid") {
          clearTimeout(timeout);
          reject(new Error(`HA auth failed: ${data.message}`));
        }
      });

      ws.addEventListener("error", () => {
        clearTimeout(timeout);
        reject(new Error("WebSocket connection error"));
      });
    });

    return ws as any;
  };
}

export async function connectToHA(): Promise<Connection> {
  const url = process.env.HA_URL || "http://localhost:8123";
  const token = process.env.HA_TOKEN;

  if (!token) {
    throw new Error("HA_TOKEN environment variable is required");
  }

  console.log(`[OPENCLAW HA] Connecting to Home Assistant at ${url}...`);
  console.log(`[OPENCLAW HA] Token present: ${!!token} (length: ${token.length})`);
  const auth = createLongLivedTokenAuth(url, token);

  connection = await createConnection({
    auth,
    createSocket: createHASocket(url, token),
  });

  connection.addEventListener("ready", () => {
    console.log("[OPENCLAW HA] WebSocket: connected and ready");
  });

  connection.addEventListener("disconnected", () => {
    console.log("[OPENCLAW HA] WebSocket: disconnected (will auto-reconnect)");
  });

  connection.addEventListener("reconnect-error", () => {
    console.error("[OPENCLAW HA] WebSocket: reconnect error");
  });

  // Subscribe to entity state changes — keeps `entities` updated in real-time
  let entityUpdateCount = 0;
  subscribeEntities(connection, (newEntities) => {
    const count = Object.keys(newEntities).length;
    entityUpdateCount++;
    if (entityUpdateCount <= 3 || entityUpdateCount % 50 === 0) {
      console.log(`[OPENCLAW HA] Entity update #${entityUpdateCount}: ${count} entities`);
    }
    entities = newEntities;
  });

  connectionReady = true;
  console.log("[OPENCLAW HA] WebSocket: authenticated and subscribed to entities");
  return connection;
}

export function isConnectionReady(): boolean {
  return connectionReady && connection !== null;
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

export async function reloadConfigEntry(entityId: string): Promise<void> {
  const url = getHAUrl();
  const token = getHAToken();
  try {
    const res = await fetch(`${url}/api/services/homeassistant/reload_config_entry`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ entity_id: entityId }),
    });
    if (!res.ok) {
      const text = await res.text().catch(() => "");
      console.log(`[OPENCLAW HA] Config entry reload for ${entityId} returned ${res.status}: ${text.slice(0, 200)}`);
    }
  } catch (err: any) {
    console.log(`[OPENCLAW HA] Failed to reload config entry for ${entityId}: ${err.message}`);
  }
}

export function getHAUrl(): string {
  return process.env.HA_URL || "http://localhost:8123";
}

export function getHAToken(): string {
  const token = process.env.HA_TOKEN;
  if (!token) {
    throw new Error("HA_TOKEN environment variable is not set. Cannot make authenticated requests to Home Assistant.");
  }
  return token;
}
