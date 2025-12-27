/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Primary: Sage Mint palette
        primary: {
          50: "#f4f9f6",
          100: "#e3efe8",
          200: "#c6ded0", // Main mint background for light cards
          300: "#9ebfaa",
          400: "#769f86",
          500: "#568368",
          600: "#426851",
          700: "#365342",
          800: "#2d4236",
          900: "#26372e",
          DEFAULT: "#568368",
          foreground: "#111111",
        },
        // Secondary: Carbon palette
        secondary: {
          50: "#f6f6f6",
          100: "#e7e7e7",
          200: "#d1d1d1",
          300: "#b0b0b0",
          400: "#888888", // Text muted
          500: "#6d6d6d",
          600: "#5d5d5d",
          700: "#4f4f4f",
          800: "#1c1c1c", // Card surface dark
          900: "#0f0f0f", // Main background
          950: "#050505",
          DEFAULT: "#1c1c1c",
          foreground: "#FFFFFF",
        },
        // Semantic colors mapping
        background: {
          DEFAULT: "#FFFFFF",
          dark: "#0f0f0f",
        },
        foreground: {
          DEFAULT: "#111111",
          dark: "#FFFFFF",
        },
        card: {
          DEFAULT: "#FFFFFF",
          dark: "#1c1c1c",
          foreground: "#111111",
          "foreground-dark": "#FFFFFF",
        },
        muted: {
          DEFAULT: "#f6f6f6",
          dark: "#1c1c1c",
          foreground: "#6d6d6d",
          "foreground-dark": "#888888",
        },
        accent: {
          DEFAULT: "#c6ded0", // Sage Mint 200
          dark: "#365342",
          foreground: "#111111",
          "foreground-dark": "#FFFFFF",
        },
        border: {
          DEFAULT: "#e7e7e7",
          dark: "#333333",
        },
        // Chart colors
        chart: {
          bar: "#FFFFFF",
          "bar-light": "#111111",
          muted: "#333333",
          "muted-light": "#d1d1d1",
        },
      },
      fontFamily: {
        sans: ["DM Sans", "Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      fontSize: {
        "hero": ["3rem", { lineHeight: "1", fontWeight: "300" }], // 48px - Big stats
        "stat": ["2rem", { lineHeight: "1.2", fontWeight: "400" }], // 32px
        "title": ["1.125rem", { lineHeight: "1.4", fontWeight: "500" }], // 18px - Card titles
        "label": ["0.75rem", { lineHeight: "1.5", fontWeight: "500", letterSpacing: "0.05em" }], // 12px - Uppercase labels
      },
      borderRadius: {
        "card": "1.5rem", // 24px - Consistent card radius
        "lg": "1rem",
        "md": "0.75rem",
        "sm": "0.5rem",
      },
      spacing: {
        "card": "1.5rem", // 24px - Card padding
        "gap": "1.5rem", // 24px - Grid gap
      },
      boxShadow: {
        "card-light": "0 4px 20px rgba(0, 0, 0, 0.08)",
        "card-mint": "0 4px 24px rgba(86, 131, 104, 0.15)",
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "fade-in": "fadeIn 0.3s ease-out",
        "slide-up": "slideUp 0.4s ease-out",
        "scale-in": "scaleIn 0.2s ease-out",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        scaleIn: {
          "0%": { opacity: "0", transform: "scale(0.95)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
      },
      maxWidth: {
        "dashboard": "1400px",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};
