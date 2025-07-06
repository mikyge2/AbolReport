/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html"
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#1a355b',
          dark: '#0f2240',
        },
        secondary: {
          DEFAULT: '#ffc72c',
          dark: '#e6b426',
        },
      },
    },
  },
  plugins: [],
};