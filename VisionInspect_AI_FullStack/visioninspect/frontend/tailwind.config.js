/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/app/**/*.{js,ts,jsx,tsx}",
    "./src/components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        graphite: "#1C1F22",
        panel: "#24282C",
        "panel-2": "#2B3035",
        line: "#383E44",
        amber: "#F5A623",
        "amber-dim": "#8a6420",
        critical: "#E4572E",
        high: "#E08A3D",
        pass: "#4FA65B",
        ink: "#EDEDED",
        muted: "#9AA0A6",
      },
      fontFamily: {
        display: ["'Space Grotesk'", "sans-serif"],
        sans: ["'Inter'", "sans-serif"],
        mono: ["'JetBrains Mono'", "monospace"],
      },
    },
  },
  plugins: [],
};
