import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        nexus: {
          bg: "#0a0a0f",
          card: "#0f0f1a",
          border: "#1a1a2e",
          cyan: "#00d4ff",
          purple: "#9b59b6",
          green: "#00ff88",
          amber: "#f59e0b",
          red: "#ef4444",
        },
      },
      fontFamily: {
        mono: ["'JetBrains Mono'", "Menlo", "monospace"],
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        typewriter: "typewriter 0.05s steps(1) forwards",
      },
    },
  },
  plugins: [],
};

export default config;
