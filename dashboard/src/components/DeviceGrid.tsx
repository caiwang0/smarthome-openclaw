import { useState } from "react";
import type { Device, Area } from "../types";
import DeviceCard from "./DeviceCard";
import LightCard from "./LightCard";
import SwitchCard from "./SwitchCard";
import ClimateCard from "./ClimateCard";
import CameraCard from "./CameraCard";
import SensorCard from "./SensorCard";
import MediaPlayerCard from "./MediaPlayerCard";

interface DeviceGridProps {
  devices: Device[];
  areas: Area[];
  selectedArea: string | null;
}

/** Numeric-only area names (e.g. "2663722756") are raw IDs, not human labels. */
function sanitizeAreaName(name: string | null): string {
  if (!name) return "Other";
  if (/^\d+$/.test(name.trim())) return "Other";
  return name;
}

// ---------------------------------------------------------------------------
// System device detection
// ---------------------------------------------------------------------------

/** Domains that are clearly system / infrastructure level */
const SYSTEM_DOMAINS = new Set([
  "sun",
  "weather",
  "tts",
  "update",
  "persistent_notification",
  "zone",
  "input_boolean",
  "input_number",
  "input_select",
  "input_text",
  "timer",
  "counter",
]);

/** Domains that represent user-controllable devices */
const INTERACTIVE_DOMAINS = new Set([
  "light",
  "switch",
  "climate",
  "camera",
  "media_player",
  "cover",
  "fan",
  "vacuum",
  "lock",
  "alarm_control_panel",
]);

/** Sensor device_class values that are genuinely user-relevant */
const USEFUL_SENSOR_CLASSES = new Set([
  "temperature",
  "humidity",
  "pressure",
  "illuminance",
  "power",
  "energy",
  "voltage",
  "current",
  "battery",
  "door",
  "window",
  "motion",
  "occupancy",
  "smoke",
  "moisture",
  "co2",
  "co",
  "pm25",
  "pm10",
  "gas",
  "connectivity",
  "sound",
]);

const MAC_RE = /([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}/;
const HCI_RE = /^hci\d+/i;
const NUM_RE = /^\d+$/;

/**
 * Returns true for devices that belong in the "System & Integrations" section
 * rather than the main dashboard — e.g. Sun, Backup Manager, Google Translate,
 * Forecast, or Bluetooth adapters named with MAC addresses.
 */
function isSystemDevice(device: Device): boolean {
  // Jargon-named devices (MAC, hci*, pure numeric) → system
  const n = device.name.trim();
  if (MAC_RE.test(n) || HCI_RE.test(n) || NUM_RE.test(n)) return true;

  // No entities at all → likely placeholder
  if (device.entities.length === 0) return true;

  // Has at least one interactive/controllable entity → user-facing
  if (device.entities.some((e) => INTERACTIVE_DOMAINS.has(e.domain))) return false;

  // All entities are in known system domains → system
  if (device.entities.every((e) => SYSTEM_DOMAINS.has(e.domain))) return true;

  // Only sensor / binary_sensor entities — check for useful device classes
  const allSensors = device.entities.every(
    (e) => e.domain === "sensor" || e.domain === "binary_sensor"
  );
  if (allSensors) {
    const hasUsefulClass = device.entities.some((e) =>
      USEFUL_SENSOR_CLASSES.has(e.attributes.device_class ?? "")
    );
    return !hasUsefulClass;
  }

  return false;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

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
    case "media_player":
      return <MediaPlayerCard device={device} />;
    case "sensor":
    case "binary_sensor":
      return <SensorCard device={device} />;
    default:
      return null;
  }
}

// Fix 6 – Empty state for rooms: show a friendly room-specific message.
function EmptyState({ roomName }: { roomName?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-24 text-center">
      <div className="w-16 h-16 rounded-2xl bg-[#FFF3E0] flex items-center justify-center mb-4">
        <svg
          className="w-8 h-8 text-[#E8913A]"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth={1.5}
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
          <polyline points="9 22 9 12 15 12 15 22" />
        </svg>
      </div>
      {roomName ? (
        <>
          <p className="text-base font-semibold text-[#2C2520]">
            No devices in {roomName} yet
          </p>
          <p className="text-sm text-[#8C7E72] mt-1">
            Assign devices to this room in your smart home hub.
          </p>
        </>
      ) : (
        <>
          <p className="text-base font-semibold text-[#2C2520]">No devices here yet</p>
          <p className="text-sm text-[#8C7E72] mt-1">
            Add devices in your smart home hub to see them here.
          </p>
        </>
      )}
    </div>
  );
}

function ChevronIcon({ open }: { open: boolean }) {
  return (
    <svg
      className={`w-4 h-4 transition-transform duration-200 ${open ? "rotate-180" : ""}`}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <polyline points="6 9 12 15 18 9" />
    </svg>
  );
}

// Fix 3 – Sparse layout: use auto-fill with a sensible min/max so cards never
// leave huge empty gaps when only 1-3 devices are present, but still expand to
// fill wide viewports gracefully.  `minmax(280px, 1fr)` lets the browser pack
// as many columns as fit while each card stays readable.  The explicit
// max-w-[420px] per card (applied in the wrapper) prevents single cards from
// stretching across the full 1800 px container.
const CARD_GRID = "grid gap-4 [grid-template-columns:repeat(auto-fill,minmax(280px,1fr))]";

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export default function DeviceGrid({ devices, areas: _areas, selectedArea }: DeviceGridProps) {
  const [showSystem, setShowSystem] = useState(false);

  let filtered = devices;
  if (selectedArea === "__unassigned__") {
    filtered = devices.filter((d) => !d.area_id);
  } else if (selectedArea) {
    filtered = devices.filter((d) => d.area_id === selectedArea);
  }

  if (filtered.length === 0) return <EmptyState />;

  // Separate user-facing from system/infrastructure devices
  const userDevices   = filtered.filter((d) => !isSystemDevice(d));
  const systemDevices = filtered.filter((d) => isSystemDevice(d));

  // Group user devices by area name
  const grouped = new Map<string, Device[]>();
  for (const device of userDevices) {
    const key  = sanitizeAreaName(device.area_name);
    const list = grouped.get(key) ?? [];
    list.push(device);
    grouped.set(key, list);
  }

  const sortedGroups = [...grouped.entries()].sort(([a], [b]) => {
    if (a === "Other") return 1;
    if (b === "Other") return -1;
    return a.localeCompare(b);
  });

  return (
    <div className="space-y-10">
      {/* ── User-facing device sections ── */}
      {sortedGroups.map(([areaName, areaDevices]) => (
        <section key={areaName}>
          {/* Room header — 24px bold, warm brown, visible from 1m+ */}
          <h2 className="text-2xl font-bold text-[#6B5E52] mb-4">{areaName}</h2>
          <div className={CARD_GRID}>
            {areaDevices.map((device, idx) => (
              <div
                key={device.id}
                className="animate-slide-up"
                style={{ animationDelay: `${idx * 50}ms`, animationFillMode: "both" }}
              >
                <DeviceCard device={device}>
                  {renderDeviceControls(device)}
                </DeviceCard>
              </div>
            ))}
          </div>
        </section>
      ))}

      {/* ── System & Integrations — collapsed by default ── */}
      {systemDevices.length > 0 && (
        <section>
          <button
            onClick={() => setShowSystem((s) => !s)}
            className="flex items-center gap-2 text-sm font-semibold text-[#8C7E72] hover:text-[#6B5E52] transition-colors mb-4 min-h-[44px] px-1"
            aria-expanded={showSystem}
          >
            <ChevronIcon open={showSystem} />
            System &amp; Integrations
            <span className="text-sm font-normal text-[#B8ADA2] ml-1">
              ({systemDevices.length})
            </span>
          </button>

          {showSystem && (
            <div className={CARD_GRID}>
              {systemDevices.map((device, idx) => (
                <div
                  key={device.id}
                  className="animate-slide-up"
                  style={{ animationDelay: `${idx * 50}ms`, animationFillMode: "both" }}
                >
                  <DeviceCard device={device}>
                    {renderDeviceControls(device)}
                  </DeviceCard>
                </div>
              ))}
            </div>
          )}
        </section>
      )}
    </div>
  );
}
