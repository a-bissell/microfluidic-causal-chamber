/**
 * Mevolut Dashboard Color System
 * 
 * Color palette based on the design brief:
 * - Primary: Sage Mint - Used for high-priority cards (Tracking, Green Energy)
 * - Secondary: Carbon - Dark mode backgrounds and surfaces
 * - Accents: White/Black for text contrast
 */

export const colors = {
  primary: {
    name: "Sage Mint",
    50: "#f4f9f6",
    100: "#e3efe8",
    200: "#c6ded0", // Main Light Background for Tracking & Green Energy cards
    300: "#9ebfaa",
    400: "#769f86",
    500: "#568368",
    600: "#426851",
    700: "#365342",
    800: "#2d4236",
    900: "#26372e",
  },
  secondary: {
    name: "Carbon",
    50: "#f6f6f6",
    100: "#e7e7e7",
    200: "#d1d1d1",
    300: "#b0b0b0",
    400: "#888888", // Text Muted
    500: "#6d6d6d",
    600: "#5d5d5d",
    700: "#4f4f4f",
    800: "#1c1c1c", // Card Surface Dark
    900: "#0f0f0f", // Main Background
    950: "#050505",
  },
  accents: {
    white: "#FFFFFF", // Primary Text on Dark
    black: "#111111", // Primary Text on Light/Mint
    chartBars: "#FFFFFF",
    chartMuted: "#333333",
  },
};

export const typography = {
  fontFamily: {
    sans: ["DM Sans", "Inter", "system-ui", "sans-serif"],
    mono: ["JetBrains Mono", "monospace"],
  },
  weights: {
    regular: 400,
    medium: 500,
    semibold: 600,
  },
  scale: {
    xs: "0.75rem", // 12px - Labels
    sm: "0.875rem", // 14px - Secondary text
    base: "1rem", // 16px - Body
    lg: "1.125rem", // 18px - Card Titles
    xl: "1.5rem", // 24px - Key stats
    "2xl": "2rem", // 32px - Large headers
    "4xl": "3rem", // 48px - Hero numbers
  },
};

export const spacing = {
  cardRadius: "1.5rem", // 24px - consistent corner radius
  gap: "1.5rem", // 24px - grid gap
};

export const breakpoints = {
  sm: "640px",
  md: "768px",
  lg: "1024px",
  xl: "1280px",
  "2xl": "1536px",
};

export default colors;

