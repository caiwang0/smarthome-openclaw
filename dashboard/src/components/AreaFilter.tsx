import type { Area } from "../types";

/** Raw numeric area IDs (e.g. "2663722756") are never user-facing labels. */
function sanitizeAreaLabel(name: string): string {
  if (/^\d+$/.test(name.trim())) return "Other";
  return name;
}

interface AreaFilterProps {
  areas: Area[];
  selectedArea: string | null;
  totalDevices: number;
  unassignedCount: number;
  onSelect: (areaId: string | null) => void;
}

export default function AreaFilter({
  areas,
  selectedArea,
  onSelect,
}: AreaFilterProps) {
  // "Unassigned" pill is intentionally omitted — unassigned devices appear
  // under "Other" in the grid. The "All" view includes them.
  return (
    <div className="flex items-center gap-2 overflow-x-auto scrollbar-hide pb-1">
      <Pill
        label="All"
        active={selectedArea === null}
        onClick={() => onSelect(null)}
      />
      {areas.map((area) => (
        <Pill
          key={area.area_id}
          label={sanitizeAreaLabel(area.name)}
          active={selectedArea === area.area_id}
          onClick={() => onSelect(area.area_id)}
        />
      ))}
    </div>
  );
}

function Pill({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={[
        "flex-shrink-0 rounded-full px-4 text-sm font-semibold transition-all duration-150",
        "min-h-[44px] leading-none whitespace-nowrap",
        active
          ? "bg-[#FFF3E0] border border-[#E8913A] text-[#D4760A]"
          : "bg-white border border-[#E8E2D9] text-[#6B5E52] hover:bg-[#F5F0EB] hover:border-[#D9D2CA]",
      ].join(" ")}
    >
      {label}
    </button>
  );
}
