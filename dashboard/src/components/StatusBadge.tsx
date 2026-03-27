interface StatusBadgeProps {
  status: "online" | "offline" | "unknown";
}

export default function StatusBadge({ status }: StatusBadgeProps) {
  if (status === "online") {
    // Online: just a subtle green pulse dot — universally understood, no text needed
    return (
      <span
        aria-label="Online"
        title="Online"
        className="w-2.5 h-2.5 rounded-full bg-[#5A9E6F] flex-shrink-0 mt-1 animate-pulse-dot"
      />
    );
  }

  if (status === "offline") {
    // Red dot + text — clearly communicates "this device cannot be reached".
    return (
      <span className="inline-flex items-center gap-1.5 flex-shrink-0 mt-0.5">
        <span className="w-2 h-2 rounded-full bg-[#C93B3B] flex-shrink-0" />
        <span className="text-sm font-semibold text-[#C93B3B] leading-none">Offline</span>
      </span>
    );
  }

  // Unknown: small gray dot, no label (non-alarming)
  return (
    <span
      aria-label="Status unknown"
      title="Status unknown"
      className="w-2.5 h-2.5 rounded-full bg-[#B8ADA2] flex-shrink-0 mt-1"
    />
  );
}
