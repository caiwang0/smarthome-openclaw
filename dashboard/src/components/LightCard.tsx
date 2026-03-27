import { useState } from "react";
import type { Device } from "../types";
import { callService } from "../api";

export default function LightCard({ device }: { device: Device }) {
  const foundEntity = device.entities.find((e) => e.domain === "light");
  if (!foundEntity) return null;
  const entity = foundEntity;

  const [optimisticOn,         setOptimisticOn]         = useState<boolean | null>(null);
  const [optimisticBrightness, setOptimisticBrightness] = useState<number | null>(null);
  const [loading,              setLoading]              = useState(false);

  const isOn             = optimisticOn ?? entity.state === "on";
  const brightness       = optimisticBrightness ?? entity.attributes.brightness ?? 0;
  const brightnessPercent = Math.round((brightness / 255) * 100);
  const disabled         = loading || device.status === "offline";

  async function toggle() {
    setLoading(true);
    setOptimisticOn(!isOn);
    try {
      await callService("light", isOn ? "turn_off" : "turn_on", {
        entity_id: entity.entity_id,
      });
    } finally {
      setLoading(false);
      setTimeout(() => setOptimisticOn(null), 2000);
    }
  }

  async function setBrightness(value: number) {
    const rawBrightness = Math.round((value / 100) * 255);
    setOptimisticBrightness(rawBrightness);
    await callService("light", "turn_on", {
      entity_id: entity.entity_id,
      brightness: rawBrightness,
    });
    setTimeout(() => setOptimisticBrightness(null), 2000);
  }

  return (
    <div className="space-y-3 pt-3 border-t border-[#E8E2D9]">
      {/* State label + toggle in one row */}
      <div className="flex items-center justify-between min-h-[44px]">
        <span className={`text-sm font-semibold ${isOn ? "text-[#E8913A]" : "text-[#B8ADA2]"}`}>
          {isOn ? `On · ${brightnessPercent}%` : "Off"}
        </span>
        <button
          role="switch"
          aria-checked={isOn}
          onClick={toggle}
          disabled={disabled}
          className={`toggle-track ${disabled ? "opacity-50 cursor-not-allowed" : ""}`}
          data-on={String(isOn)}
        >
          <div className="toggle-thumb" />
        </button>
      </div>

      {/* Brightness slider — only when light is on */}
      {isOn && (
        <div className="space-y-1.5">
          <input
            type="range"
            min={1}
            max={100}
            value={brightnessPercent}
            disabled={disabled}
            onChange={(e) => setBrightness(Number(e.target.value))}
            className="w-full"
            aria-label="Brightness"
          />
          <div className="flex items-center justify-between">
            <span className="text-sm text-[#8C7E72] font-semibold">Brightness</span>
            <span className="text-base font-semibold text-[#E8913A] tabular-nums">
              {brightnessPercent}%
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
