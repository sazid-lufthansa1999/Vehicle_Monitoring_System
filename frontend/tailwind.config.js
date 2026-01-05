/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        dark: "#020617",
        navy: "#0f172a",
        accent: "#38bdf8",
        danger: "#ef4444",
        success: "#10b981",
      },
    },
  },
  plugins: [],
}
