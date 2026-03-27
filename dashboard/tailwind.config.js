/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // Base warm palette
        "warm-bg":      "#FAF8F5",
        "warm-card":    "#FFFFFF",
        "warm-active":  "#FFF8ED",
        "warm-border":  "#E8E2D9",
        "warm-divider": "#D9D2CA",
        // Text
        "text-primary":   "#2C2520",
        "text-secondary": "#8C7E72",
        "text-muted":     "#B8ADA2",
        "text-room":      "#6B5E52",
        // Semantic
        amber:   "#E8913A",
        "amber-light": "#FFF3E0",
        "amber-dark":  "#D4760A",
        heat:    "#E8653A",
        cool:    "#5BA4CF",
        success: "#5A9E6F",
        danger:  "#C93B3B",
        warning: "#D4760A",
        // Legacy aliases kept so existing Tailwind classes still compile
        black:  "#0A0A0A",
        mid:    "#6B6B6B",
        dim:    "#3A3A3A",
      },
      fontFamily: {
        // Both sans and mono → Nunito Sans so font-mono classes auto-upgrade
        sans: ["Nunito Sans", "system-ui", "sans-serif"],
        mono: ["Nunito Sans", "system-ui", "sans-serif"],
      },
      animation: {
        "fade-in":  "fadeIn 0.25s ease-out",
        "slide-up": "slideUp 0.25s ease-out",
        blink:      "blink 1s step-end infinite",
        "pulse-dot": "pulseDot 2s ease-in-out infinite",
      },
      keyframes: {
        fadeIn: {
          "0%":   { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%":   { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        blink: {
          "0%, 100%": { opacity: "1" },
          "50%":      { opacity: "0" },
        },
        pulseDot: {
          "0%, 100%": { opacity: "1",   transform: "scale(1)" },
          "50%":      { opacity: "0.6", transform: "scale(1.3)" },
        },
      },
    },
  },
  plugins: [],
};
