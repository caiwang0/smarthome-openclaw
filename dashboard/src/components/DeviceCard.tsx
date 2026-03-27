import type { Device } from "../types";
import StatusBadge from "./StatusBadge";
import { DeviceIcon } from "./DeviceIcon";

/** Patterns that indicate a technical/jargon device name, not a friendly label */
const MAC_PATTERN     = /([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}/;
const HCI_PATTERN     = /^hci\d+/i;
const NUMERIC_PATTERN = /^\d+$/;

function sanitizeDeviceName(name: string): string {
  const trimmed = name.trim();
  if (MAC_PATTERN.test(trimmed))     return "Unknown Device";
  if (HCI_PATTERN.test(trimmed))     return "Unknown Device";
  if (NUMERIC_PATTERN.test(trimmed)) return "Unknown Device";
  return name;
}

function isDeviceActive(device: Device): boolean {
  return (
    device.entities.some((e) => e.domain === "light"        && e.state === "on") ||
    device.entities.some((e) => e.domain === "switch"       && e.state === "on") ||
    device.entities.some((e) => e.domain === "media_player" && (e.state === "playing" || e.state === "idle" || e.state === "paused")) ||
    device.entities.some((e) => e.domain === "climate"      && e.state !== "off")
  );
}

interface DeviceCardProps {
  device: Device;
  children?: React.ReactNode;
}

export default function DeviceCard({ device, children }: DeviceCardProps) {
  const active = isDeviceActive(device);

  return (
    <div
      className={`card flex flex-col gap-3 relative animate-fade-in h-full ${active ? "card-active" : ""}`}
      style={active ? {
        background:     "#FFF8ED",
        borderColor:    "#E8913A",
        borderLeftWidth: "4px",
        boxShadow:      "0 4px 12px rgba(232, 145, 58, 0.15)",
      } : undefined}
    >
      {/* "New" badge — soft warm pill, not a harsh neon block */}
      {device.is_new && (
        <span className="absolute -top-2 -right-2 bg-[#E8913A] text-white text-xs font-bold rounded-full px-2.5 py-0.5 shadow-sm">
          New
        </span>
      )}

      {/* Device header row */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-3 min-w-0">
          <DeviceIcon type={device.device_type} isActive={active} className="flex-shrink-0" />
          <div className="min-w-0">
            <h3 className="text-base font-semibold text-[#2C2520] truncate leading-snug">
              {sanitizeDeviceName(device.name)}
            </h3>
            {device.manufacturer && (
              <p className="text-sm text-[#8C7E72] truncate leading-snug mt-0.5">
                {device.manufacturer}
                {device.model ? ` · ${device.model}` : ""}
              </p>
            )}
          </div>
        </div>
        <StatusBadge status={device.status} />
      </div>

      {/* MAC / IP addresses are intentionally hidden from the default view.
          Technical connection info isn't useful to regular home users. */}

      {/* Device-specific controls */}
      {children}
    </div>
  );
}
