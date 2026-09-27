/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#0b1220",
          900: "#111827",
          800: "#1f2937",
          700: "#374151",
          600: "#4b5563",
          400: "#9ca3af",
          200: "#e5e7eb",
          100: "#f3f4f6",
          50: "#f8fafc",
        },
        brand: {
          700: "#1d4ed8",
          600: "#2563eb",
          500: "#3b82f6",
          100: "#dbeafe",
        },
        risk: {
          high: "#dc2626",
          medium: "#d97706",
          low: "#16a34a",
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "ui-sans-serif", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
