/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./pages/**/*.{js,jsx}", "./components/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ember: {
          50: "#fff7ed",
          100: "#ffedd5",
          500: "#f97316",
          700: "#c2410c"
        },
        ocean: {
          50: "#ecfeff",
          100: "#cffafe",
          600: "#0891b2",
          800: "#155e75"
        },
        slateink: "#1f2937"
      },
      boxShadow: {
        panel: "0 20px 45px -25px rgba(15, 23, 42, 0.35)"
      },
      animation: {
        rise: "rise 450ms ease-out",
        pulseSoft: "pulseSoft 1.5s ease-in-out infinite"
      },
      keyframes: {
        rise: {
          "0%": { opacity: "0", transform: "translateY(12px)" },
          "100%": { opacity: "1", transform: "translateY(0)" }
        },
        pulseSoft: {
          "0%, 100%": { opacity: "0.45" },
          "50%": { opacity: "1" }
        }
      }
    },
  },
  plugins: [],
};
