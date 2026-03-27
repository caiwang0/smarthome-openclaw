import { useState } from "react";
import type { Device } from "../types";
import { callService } from "../api";

function PlayIcon() {
  return (
    <svg className="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
      <polygon points="5 3 19 12 5 21 5 3" />
    </svg>
  );
}

function PauseIcon() {
  return (
    <svg className="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
      <rect x="6"  y="4" width="4" height="16" rx="1" />
      <rect x="14" y="4" width="4" height="16" rx="1" />
    </svg>
  );
}

function VolumeDownIcon() {
  return (
    <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
      <line x1="15" y1="9" x2="15" y2="15" />
    </svg>
  );
}

function VolumeUpIcon() {
  return (
    <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
      <path d="M15.54 8.46a5 5 0 0 1 0 7.07" />
      <path d="M19.07 4.93a10 10 0 0 1 0 14.14" />
    </svg>
  );
}

export default function MediaPlayerCard({ device }: { device: Device }) {
  const foundEntity = device.entities.find((e) => e.domain === "media_player");
  if (!foundEntity) return null;
  const entity = foundEntity;

  const [loading, setLoading] = useState(false);

  const state      = entity.state;
  const volume     = entity.attributes.volume_level;
  const mediaTitle = entity.attributes.media_title;

  async function sendCommand(service: string, data: Record<string, unknown> = {}) {
    setLoading(true);
    try {
      await callService("media_player", service, {
        entity_id: entity.entity_id,
        ...data,
      });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-3 pt-3 border-t border-[#E8E2D9]">
      {/* Now playing */}
      {mediaTitle && (
        <p className="text-sm text-[#E8913A] font-semibold truncate">
          ♪ {mediaTitle}
        </p>
      )}

      {state === "unavailable" && (
        <p className="text-sm text-[#8C7E72]">May be sleeping — commands still work</p>
      )}

      {/* Controls row */}
      <div className="flex items-center justify-center gap-3">
        {/* Volume down — 48×48 touch target */}
        <button
          onClick={() => sendCommand("volume_down")}
          disabled={loading}
          aria-label="Volume down"
          className="btn w-12 h-12 p-0 rounded-xl text-[#8C7E72] hover:text-[#2C2520] disabled:opacity-50"
        >
          <VolumeDownIcon />
        </button>

        {/* Play / Pause — 56×56, amber circle */}
        <button
          onClick={() => sendCommand("media_play_pause")}
          disabled={loading}
          aria-label={state === "playing" ? "Pause" : "Play"}
          className="w-14 h-14 rounded-full bg-[#E8913A] text-white flex items-center justify-center shadow-md hover:bg-[#D4760A] active:scale-95 transition-all duration-150 disabled:opacity-50 flex-shrink-0"
        >
          {state === "playing" ? <PauseIcon /> : <PlayIcon />}
        </button>

        {/* Volume up — 48×48 touch target */}
        <button
          onClick={() => sendCommand("volume_up")}
          disabled={loading}
          aria-label="Volume up"
          className="btn w-12 h-12 p-0 rounded-xl text-[#8C7E72] hover:text-[#2C2520] disabled:opacity-50"
        >
          <VolumeUpIcon />
        </button>
      </div>

      {/* Volume level */}
      {volume != null && (
        <p className="text-sm text-[#8C7E72] text-center tabular-nums">
          Volume {Math.round(volume * 100)}%
        </p>
      )}
    </div>
  );
}
