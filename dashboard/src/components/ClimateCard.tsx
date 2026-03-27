import { useState } from "react";
import type { Device } from "../types";
import { callService } from "../api";

function capitalize(s: string) {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

export default function ClimateCard({ device }: { device: Device }) {
  const foundEntity = device.entities.find((e) => e.domain === "climate");
  if (!foundEntity) return null;
  const entity = foundEntity;

  const currentTemp  = entity.attributes.current_temperature;
  const targetTemp   = entity.attributes.temperature;
  const hvacMode     = entity.state;
  const hvacModes: string[] = entity.attributes.hvac_modes || [];
  const minTemp      = entity.attributes.min_temp ?? 16;
  const maxTemp      = entity.attributes.max_temp ?? 30;
  const unit         = entity.attributes.temperature_unit || "\u00b0C";

  const [loading, setLoading] = useState(false);
  const disabled = loading || device.status === "offline";

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

  // Temperature colour by mode
  const tempColor =
    hvacMode === "heat" ? "text-[#E8653A]" :
    hvacMode === "cool" ? "text-[#5BA4CF]" :
    hvacMode === "off"  ? "text-[#B8ADA2]" :
                          "text-[#2C2520]";

  return (
    <div className="space-y-3 pt-3 border-t border-[#E8E2D9]">
      {/* Current temp label */}
      {currentTemp != null && (
        <p className="text-sm text-[#8C7E72]">
          Currently <span className="font-semibold text-[#2C2520]">{currentTemp}{unit}</span>
        </p>
      )}

      {/* Target temp with large ± buttons (48 px touch targets) */}
      <div className="flex items-center justify-center gap-4">
        <button
          onClick={() => setTemp(-0.5)}
          disabled={disabled}
          aria-label="Decrease temperature"
          className="btn w-12 h-12 text-xl p-0 flex items-center justify-center rounded-xl disabled:opacity-50"
        >
          −
        </button>

        <span className={`text-4xl font-bold tabular-nums leading-none w-28 text-center ${tempColor}`}>
          {targetTemp != null ? `${targetTemp}${unit}` : "—"}
        </span>

        <button
          onClick={() => setTemp(0.5)}
          disabled={disabled}
          aria-label="Increase temperature"
          className="btn w-12 h-12 text-xl p-0 flex items-center justify-center rounded-xl disabled:opacity-50"
        >
          +
        </button>
      </div>

      {/* Mode pills */}
      {hvacModes.length > 0 && (
        <div className="flex gap-2 flex-wrap">
          {hvacModes.map((mode) => (
            <button
              key={mode}
              onClick={() => setMode(mode)}
              disabled={disabled}
              className={`btn rounded-full py-1.5 px-3 text-sm disabled:opacity-50 ${hvacMode === mode ? "btn-active" : ""}`}
            >
              {capitalize(mode)}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
