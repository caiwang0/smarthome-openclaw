import { useState, useEffect } from "react";

interface NotificationToastProps {
  deviceNames: string[];
}

function CloseIcon() {
  return (
    <svg
      className="w-4 h-4"
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

function HomeNewIcon() {
  return (
    <svg
      className="w-5 h-5 text-[#E8913A] flex-shrink-0"
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

export default function NotificationToast({ deviceNames }: NotificationToastProps) {
  const [visible,        setVisible]        = useState(false);
  const [displayedNames, setDisplayedNames] = useState<string[]>([]);

  useEffect(() => {
    if (deviceNames.length > 0 && deviceNames.join(",") !== displayedNames.join(",")) {
      setDisplayedNames(deviceNames);
      setVisible(true);
      const timer = setTimeout(() => setVisible(false), 8_000);
      return () => clearTimeout(timer);
    }
  }, [deviceNames, displayedNames]);

  if (!visible || displayedNames.length === 0) return null;

  return (
    <div className="fixed top-4 right-4 z-50 max-w-sm w-full animate-slide-up">
      <div
        className="bg-white rounded-2xl border border-[#E8E2D9] shadow-lg overflow-hidden"
        style={{ borderLeftWidth: "4px", borderLeftColor: "#E8913A" }}
      >
        <div className="px-4 py-4 flex items-start gap-3">
          <HomeNewIcon />
          <div className="flex-1 min-w-0">
            <p className="text-base font-semibold text-[#2C2520]">
              New device found!
            </p>
            {displayedNames.map((name) => (
              <p key={name} className="text-sm text-[#E8913A] font-semibold mt-0.5 truncate">
                {name}
              </p>
            ))}
          </div>
          <button
            onClick={() => setVisible(false)}
            aria-label="Dismiss"
            className="w-8 h-8 flex items-center justify-center rounded-lg text-[#8C7E72] hover:bg-[#F5F0EB] hover:text-[#2C2520] transition-colors flex-shrink-0"
          >
            <CloseIcon />
          </button>
        </div>
      </div>
    </div>
  );
}
