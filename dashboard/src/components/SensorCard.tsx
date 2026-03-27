import type { Device } from "../types";
import { SensorIcon } from "./DeviceIcon";

const binaryLabels: Record<string, [string, string]> = {
  motion:    ["Motion detected", "Clear"],
  door:      ["Open",     "Closed"],
  window:    ["Open",     "Closed"],
  occupancy: ["Occupied", "Clear"],
  smoke:     ["Detected", "Clear"],
  moisture:  ["Wet",      "Dry"],
};

/** True when the state string is an ISO 8601 / date-time value. */
function isTimestamp(state: string): boolean {
  return /^\d{4}-\d{2}-\d{2}[T ]/.test(state);
}

/** Format an ISO timestamp into a friendly local time (or "Tomorrow HH:MM" etc.). */
function formatTimestamp(state: string): string {
  try {
    const date = new Date(state);
    if (isNaN(date.getTime())) return state;

    const now      = new Date();
    const today    = new Date(now.getFullYear(),   now.getMonth(),   now.getDate());
    const tomorrow = new Date(today.getTime() + 86_400_000);
    const dateDay  = new Date(date.getFullYear(),  date.getMonth(),  date.getDate());

    const timeStr = date.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });

    if (dateDay.getTime() === today.getTime())    return timeStr;
    if (dateDay.getTime() === tomorrow.getTime()) return `Tomorrow ${timeStr}`;
    return (
      date.toLocaleDateString([], { month: "short", day: "numeric" }) +
      " " +
      timeStr
    );
  } catch {
    return state;
  }
}

/**
 * Parse the entity state into a display string and an optional numeric value.
 * Returns null for numericValue when the state is not a plain number.
 */
function parseSensorState(
  state: string,
  unit: string,
): { display: string; numericValue: number | null } {
  if (state === "unknown" || state === "unavailable") {
    return { display: "—", numericValue: null };
  }

  // ISO date / datetime → format as human time
  if (isTimestamp(state)) {
    return { display: formatTimestamp(state), numericValue: null };
  }

  // Pure numeric
  const num = parseFloat(state);
  if (!isNaN(num) && isFinite(num)) {
    const display = `${Number.isInteger(num) ? num : num.toFixed(1)}${unit}`;
    return { display, numericValue: num };
  }

  // Non-numeric string (e.g. "ok", "idle", "Backup failed") — capitalise & truncate
  const cleaned = state.charAt(0).toUpperCase() + state.slice(1);
  return {
    display: cleaned.length > 22 ? cleaned.substring(0, 20) + "…" : cleaned,
    numericValue: null,
  };
}

function getSensorValueStyle(deviceClass: string, numericValue: number | null): string {
  if (numericValue === null) return "text-[#2C2520] font-semibold";
  if (deviceClass === "battery"     && numericValue < 20) return "text-[#D4760A] font-semibold tabular-nums"; // amber warning
  if (deviceClass === "temperature" && numericValue > 30) return "text-[#E8653A] font-semibold tabular-nums"; // warm heat
  if (deviceClass === "temperature" && numericValue < 10) return "text-[#5BA4CF] font-semibold tabular-nums"; // cool blue
  return "text-[#2C2520] font-semibold tabular-nums";
}

export default function SensorCard({ device }: { device: Device }) {
  const sensors = device.entities.filter(
    (e) => e.domain === "sensor" || e.domain === "binary_sensor"
  );
  if (sensors.length === 0) return null;

  return (
    <div className="space-y-0 pt-3 border-t border-[#E8E2D9]">
      {sensors.map((entity) => {
        const deviceClass = entity.attributes.device_class || "default";
        const unit        = entity.attributes.unit_of_measurement || "";

        if (entity.domain === "binary_sensor") {
          const labels = binaryLabels[deviceClass] || ["On", "Off"];
          const isOn   = entity.state === "on";
          return (
            <div
              key={entity.entity_id}
              className="flex items-center justify-between min-h-[44px] py-1"
            >
              <span className="text-sm text-[#8C7E72] flex items-center gap-2">
                <SensorIcon type={deviceClass} />
                {entity.attributes.friendly_name || deviceClass}
              </span>
              <span className={`text-sm ${isOn ? "text-[#E8913A] font-semibold" : "text-[#B8ADA2] font-medium"}`}>
                {isOn ? labels[0] : labels[1]}
              </span>
            </div>
          );
        }

        const { display, numericValue } = parseSensorState(entity.state, unit);

        return (
          <div
            key={entity.entity_id}
            className="flex items-center justify-between min-h-[44px] py-1"
          >
            <span className="text-sm text-[#8C7E72] flex items-center gap-2">
              <SensorIcon type={deviceClass} />
              {entity.attributes.friendly_name || deviceClass}
            </span>
            <span className={`text-base ${getSensorValueStyle(deviceClass, numericValue)}`}>
              {display}
            </span>
          </div>
        );
      })}
    </div>
  );
}
