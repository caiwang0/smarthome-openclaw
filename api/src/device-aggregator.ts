import {
  fetchDeviceRegistry,
  fetchEntityRegistry,
  fetchAreaRegistry,
  getEntities,
} from "./ha-client";
import type {
  AggregatedDevice,
  DeviceEntity,
  Area,
  HAEntity,
} from "./types";

let previousDeviceIds: Set<string> = new Set();
let newDeviceIds: Set<string> = new Set();
let newDeviceTimestamps: Map<string, number> = new Map();

const NEW_DEVICE_TTL_MS = 5 * 60 * 1000; // Show "NEW" badge for 5 minutes

function getDomain(entityId: string): string {
  return entityId.split(".")[0];
}

function determineDeviceType(entityDomains: string[]): string {
  const priority = ["camera", "climate", "light", "switch", "media_player", "sensor", "binary_sensor"];
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
        break;
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

  const deviceAreaMap = new Map<string, string | null>();
  for (const device of devices) {
    if (!device.disabled_by) {
      deviceAreaMap.set(device.id, device.area_id);
    }
  }

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
