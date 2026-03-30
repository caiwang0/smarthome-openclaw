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

export async function sendChatMessage(
  message: string,
  onText: (text: string) => void,
  onDone: () => void,
  onError: (error: string) => void,
  signal?: AbortSignal
): Promise<void> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
    signal,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ error: "Request failed" }));
    onError(body.error || `Chat request failed: ${res.status}`);
    return;
  }

  if (!res.body) {
    onError("No response body");
    return;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const data = line.slice(6).trim();
      if (data === "[DONE]") {
        onDone();
        return;
      }
      try {
        const parsed = JSON.parse(data);
        const delta = parsed.choices?.[0]?.delta?.content;
        if (delta) onText(delta);
      } catch {
        // Skip malformed events
      }
    }
  }
  onDone();
}
