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
      screens: {
        'xs': '475px',
        'sm': '640px',
        'md': '768px',
        'lg': '1024px',
        'xl': '1280px',
        '2xl': '1536px',
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '128': '32rem',
      },
      fontSize: {
        'xxs': '0.625rem',
      },
      minHeight: {
        'screen-mobile': 'calc(100vh - 4rem)',
      },
      maxWidth: {
        'mobile': '100vw',
      },
    },
  },
  plugins: [],
};