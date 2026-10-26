/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#fdf8f6',
          100: '#f2e8e5',
          200: '#eaddd7',
          500: '#c27848',
          600: '#a3582d',
          700: '#844220',
          800: '#69351c',
          900: '#4e2714',
        },
        slate: {
          850: '#151e2e',
        }
      }
    },
  },
  plugins: [],
}
