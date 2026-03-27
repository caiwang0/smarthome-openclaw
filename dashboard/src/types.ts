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
