/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Poker-themed color palette
        felt: {
          DEFAULT: "#0d5c2e",
          dark: "#0a4a25",
          light: "#117a3e",
        },
        card: {
          DEFAULT: "#ffffff",
          back: "#1a3a5c",
        },
        chip: {
          red: "#e53935",
          blue: "#1e88e5",
          green: "#43a047",
          black: "#212121",
          white: "#fafafa",
        },
        accent: {
          gold: "#ffc107",
          silver: "#9e9e9e",
          bronze: "#cd7f32",
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "monospace"],
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "spin-slow": "spin 3s linear infinite",
      },
    },
  },
  plugins: [],
};
