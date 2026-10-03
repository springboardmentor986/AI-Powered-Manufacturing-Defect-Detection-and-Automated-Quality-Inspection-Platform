import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0E1116",
        panel: "#161A21",
        line: "#272D36",
        ink: "#E7E9EC",
        muted: "#9AA0A6",
        amber: "#F0B43C",
        critical: "#E5484D",
        high: "#F0924A",
        medium: "#38C9C9",
        pass: "#4CB782",
      },
    },
  },
  plugins: [],
};
export default config;
