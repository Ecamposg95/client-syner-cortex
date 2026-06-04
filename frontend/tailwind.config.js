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
        // Premium slate/indigo brand colors
        brand: {
          50: '#f4f6fb',
          100: '#e8eef6',
          200: '#ccd9ea',
          300: '#a0bad8',
          400: '#6d94c1',
          500: '#4a75a7',
          600: '#395e8d',
          700: '#2f4c74',
          800: '#2a4161',
          900: '#263852',
          950: '#192437',
        },
        cortex: {
          purple: '#8B5CF6',
          pink: '#EC4899',
          indigo: '#6366F1',
          darkBg: '#0B0F19',
          darkCard: '#151D30',
        }
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        display: ['Outfit', 'sans-serif'],
      },
      boxShadow: {
        glass: '0 8px 32px 0 rgba(31, 38, 135, 0.07)',
        'glass-hover': '0 8px 32px 0 rgba(31, 38, 135, 0.15)',
        glow: '0 0 20px rgba(139, 92, 246, 0.15)',
      },
      backdropBlur: {
        xs: '2px',
      }
    },
  },
  plugins: [],
}
