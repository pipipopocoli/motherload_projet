import type { Config } from "tailwindcss";
const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        paper: "#F3EBDD",
        ink: "#141414",
        forest: "#0E3B2E",
        brass: "#B08D57",
        "forest-light": "#1A5A43",
        "paper-dark": "#EFE3D1",
        muted: "#3A3A3A",
      },
      fontFamily: {
        sans: ["var(--font-inter)"],
        serif: ["var(--font-spectral)"],
        mono: ["var(--font-mono)"],
      },
      backgroundImage: {
        "noise": "url('/noise.png')",
      },
    },
  },
  plugins: [],
};
export default config;
