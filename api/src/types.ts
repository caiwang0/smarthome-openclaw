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
