/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: {
          50: '#f5f7fa',
          100: '#e9edf2',
          300: '#aeb7c4',
          400: '#8591a2',
          500: '#647084',
          600: '#4b586c',
          700: '#334055',
          800: '#202b3d',
          900: '#131b2a',
        },
        brand: {
          50: '#eef9f6',
          100: '#d7f1e9',
          500: '#16856b',
          600: '#0f705b',
          700: '#105b4c',
        },
      },
      boxShadow: {
        soft: '0 12px 40px rgba(15, 23, 42, .08)',
      },
    },
  },
  plugins: [],
};
