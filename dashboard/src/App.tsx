import { useState } from "react";
import { useDevices } from "./hooks/useDevices";
import { useAreas } from "./hooks/useAreas";
import AreaFilter from "./components/AreaFilter";
import DeviceGrid from "./components/DeviceGrid";
import NotificationToast from "./components/NotificationToast";

function HomeIcon() {
  return (
    <svg
      className="w-6 h-6 text-[#E8913A]"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
      <polyline points="9 22 9 12 15 12 15 22" />
    </svg>
  );
}

export default function App() {
  const { devices, newDeviceNames, loading, error } = useDevices();
  const { areas } = useAreas();
  const [selectedArea, setSelectedArea] = useState<string | null>(null);

  const unassignedCount = devices.filter((d) => !d.area_id).length;

  const activeCount = devices.filter((d) =>
    d.entities.some(
      (e) =>
        (e.domain === "light"        && e.state === "on") ||
        (e.domain === "switch"       && e.state === "on") ||
        (e.domain === "media_player" && e.state === "playing") ||
        (e.domain === "climate"      && e.state !== "off")
    )
  ).length;

  function getSubtitle() {
    if (loading) {
      return (
        <span className="inline-flex items-center gap-2 text-[#8C7E72]">
          <span className="w-2 h-2 rounded-full bg-[#E8913A] animate-pulse inline-block" />
          Loading…
        </span>
      );
    }
    if (error) {
      return <span className="text-[#C93B3B]">Could not reach hub</span>;
    }
    if (devices.length === 0) return <span className="text-[#B8ADA2]">No devices yet</span>;
    if (activeCount === 0) return <span className="text-[#8C7E72]">Everything is off</span>;
    return (
      <span className="text-[#8C7E72]">
        <span className="text-[#E8913A] font-semibold">{activeCount}</span>
        {" "}
        {activeCount === 1 ? "device" : "devices"} on
      </span>
    );
  }

  return (
    <div className="min-h-screen bg-[#FAF8F5] text-[#2C2520] font-sans">
      <NotificationToast deviceNames={newDeviceNames} />

      {/* ── Header (sticky — title row + filter pills stay pinned while scrolling) ── */}
      <header className="sticky top-0 z-40 bg-[#FAF8F5]/95 backdrop-blur-sm border-b border-[#E8E2D9]">
        <div className="max-w-[1800px] mx-auto px-4">
          {/* Title row */}
          <div className="flex items-center justify-between gap-4 pt-4 pb-3">
            <div className="flex items-center gap-3">
              <HomeIcon />
              <div>
                <h1 className="text-2xl font-bold text-[#2C2520] leading-tight">
                  My Home
                </h1>
                <p className="text-sm leading-tight mt-0.5">{getSubtitle()}</p>
              </div>
            </div>
          </div>

          {/* Area filter pills — pinned with header so room switching is always accessible */}
          <div className="pb-3">
            <AreaFilter
              areas={areas}
              selectedArea={selectedArea}
              totalDevices={devices.length}
              unassignedCount={unassignedCount}
              onSelect={setSelectedArea}
            />
          </div>
        </div>
      </header>

      {/*
        Fix 1 – Sticky header scroll bug:
        The header height is roughly 110–120 px on desktop (title row ~64 px + pill row ~56 px).
        We set an explicit `pt-6` plus a safe `scroll-mt` so anchored headings are never
        obscured, and we raise main above the background so it's always rendered above the
        header's backdrop-blur layer via z-index ordering (main z-0, header z-40).
      */}
      <main className="px-4 pt-6 pb-10 max-w-[1800px] mx-auto relative z-0">
        <DeviceGrid
          devices={devices}
          areas={areas}
          selectedArea={selectedArea}
        />
      </main>
    </div>
  );
}
