import { useState } from "react";
import type { Device } from "../types";
import { callService } from "../api";

export default function SwitchCard({ device }: { device: Device }) {
  const foundEntity = device.entities.find((e) => e.domain === "switch");
  if (!foundEntity) return null;
  const entity = foundEntity;

  const [optimisticOn, setOptimisticOn] = useState<boolean | null>(null);
  const [loading,      setLoading]      = useState(false);

  const isOn     = optimisticOn ?? entity.state === "on";
  const disabled = loading || device.status === "offline";

  async function toggle() {
    setLoading(true);
    setOptimisticOn(!isOn);
    try {
      await callService("switch", "toggle", {
        entity_id: entity.entity_id,
      });
    } finally {
      setLoading(false);
      setTimeout(() => setOptimisticOn(null), 2000);
    }
  }

  return (
    <div className="pt-3 border-t border-[#E8E2D9]">
      {/* Full row is tappable — large touch target */}
      <button
        role="switch"
        aria-checked={isOn}
        onClick={toggle}
        disabled={disabled}
        className="w-full flex items-center justify-between min-h-[44px] -mx-1 px-1 rounded-xl transition-colors hover:bg-[#F5F0EB] active:bg-[#FFF3E0] disabled:cursor-not-allowed disabled:opacity-50"
      >
        <span className={`text-sm font-semibold ${isOn ? "text-[#E8913A]" : "text-[#B8ADA2]"}`}>
          {isOn ? "On" : "Off"}
        </span>
        {/* Visual toggle (aria-hidden since the button already has role/checked) */}
        <span
          aria-hidden="true"
          className={`toggle-track pointer-events-none ${disabled ? "opacity-50" : ""}`}
          data-on={String(isOn)}
        >
          <span className="toggle-thumb" />
        </span>
      </button>
    </div>
  );
}
