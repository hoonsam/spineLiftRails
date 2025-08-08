/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        gray: {
          850: '#1a1f2e',
          950: '#0a0e1a'
        }
      }
    },
  },
  plugins: [],
}