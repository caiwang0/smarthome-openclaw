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
