import { useState, useEffect } from "react";
import type { Device } from "../types";
import { cameraSnapshotUrl } from "../api";

function ExpandIcon() {
  return (
    <svg
      className="w-6 h-6 text-white drop-shadow-md"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <polyline points="15 3 21 3 21 9" />
      <polyline points="9 21 3 21 3 15" />
      <line x1="21" y1="3"  x2="14" y2="10" />
      <line x1="3"  y1="21" x2="10" y2="14" />
    </svg>
  );
}

function CloseIcon() {
  return (
    <svg
      className="w-5 h-5"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <line x1="18" y1="6"  x2="6"  y2="18" />
      <line x1="6"  y1="6"  x2="18" y2="18" />
    </svg>
  );
}

export default function CameraCard({ device }: { device: Device }) {
  const entity = device.entities.find((e) => e.domain === "camera");
  if (!entity) return null;

  const [enlarged, setEnlarged] = useState(false);
  const [imgKey,   setImgKey]   = useState(Date.now());
  const [hovered,  setHovered]  = useState(false);

  useEffect(() => {
    const interval = setInterval(() => setImgKey(Date.now()), 10_000);
    return () => clearInterval(interval);
  }, []);

  const snapshotUrl = cameraSnapshotUrl(entity.entity_id) + `&k=${imgKey}`;

  return (
    <>
      {/* Thumbnail */}
      <div
        className="pt-3 border-t border-[#E8E2D9] cursor-pointer"
        onClick={() => setEnlarged(true)}
      >
        <div
          className="relative overflow-hidden rounded-xl"
          onMouseEnter={() => setHovered(true)}
          onMouseLeave={() => setHovered(false)}
        >
          <img
            src={snapshotUrl}
            alt={device.name}
            className="w-full h-36 object-cover"
            onError={(e) => {
              (e.target as HTMLImageElement).style.display = "none";
            }}
          />
          {/* Hover overlay — warm dark, not pure black */}
          <div
            className={`absolute inset-0 flex items-center justify-center transition-opacity duration-200 ${hovered ? "opacity-100" : "opacity-0"}`}
            style={{ background: "rgba(44, 37, 32, 0.55)" }}
          >
            <ExpandIcon />
          </div>
        </div>
      </div>

      {/* Full-screen enlarged view */}
      {enlarged && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-6 animate-fade-in"
          style={{ background: "rgba(44, 37, 32, 0.92)" }}
          onClick={() => setEnlarged(false)}
        >
          {/* Close button */}
          <button
            onClick={() => setEnlarged(false)}
            aria-label="Close"
            className="absolute top-4 right-4 w-10 h-10 rounded-full bg-white/20 hover:bg-white/30 text-white flex items-center justify-center transition-colors"
          >
            <CloseIcon />
          </button>

          <div
            className="max-w-4xl w-full"
            onClick={(e) => e.stopPropagation()}
          >
            <img
              src={snapshotUrl}
              alt={device.name}
              className="w-full rounded-2xl shadow-2xl"
            />
            <p className="text-base font-semibold text-white/80 mt-4 text-center">
              {device.name}
            </p>
          </div>
        </div>
      )}
    </>
  );
}
