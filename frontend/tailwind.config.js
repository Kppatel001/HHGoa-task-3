/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        base: {
          900: "#070b16",
          800: "#0b1120",
          700: "#111a2e",
          600: "#1a2540",
        },
        accent: {
          blue: "#38bdf8",
          purple: "#a78bfa",
          green: "#34d399",
          amber: "#fbbf24",
          red: "#f87171",
        },
      },
      fontFamily: {
        mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      boxShadow: {
        glow: "0 0 40px -10px rgba(56, 189, 248, 0.35)",
        "glow-purple": "0 0 40px -10px rgba(167, 139, 250, 0.35)",
      },
      backgroundImage: {
        grid: "linear-gradient(rgba(56,189,248,0.06) 1px, transparent 1px), linear-gradient(90deg, rgba(56,189,248,0.06) 1px, transparent 1px)",
      },
      keyframes: {
        pulseGlow: {
          "0%, 100%": { opacity: "0.6" },
          "50%": { opacity: "1" },
        },
      },
      animation: {
        pulseGlow: "pulseGlow 1.6s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
