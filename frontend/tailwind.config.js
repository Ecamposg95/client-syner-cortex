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
        brand: {
          bg:          '#fafbfc',
          surface:     '#ffffff',
          surface2:    '#f4f6f8',
          accent:      '#2c9aa6',
          accentHover: '#1e6c75',
          accentBright:'#62a0aa',
          accentTint:  '#f0f8f9',
          ink:         '#0d1418',
          ink2:        '#2d383e',
          muted:       '#5c6a71',
          muted2:      '#8fa0a8',
          border:      '#e6ecef',
          borderStrong:'#c2d1d8',
          pos:         '#4ca374',
          warn:        '#c29938',
          neg:         '#e05252',
        },
        dark: {
          bg:       '#0d1418',
          bg2:      '#080c0f',
          surface:  '#141c22',
          surface2: '#19232a',
          border:   '#1e2930',
          border2:  '#283741',
          fg:       '#f3f6f7',
          muted:    '#8496a0',
          muted2:   '#5c6c75',
        }
      },
      fontFamily: {
        sans:  ['"Plus Jakarta Sans"', 'system-ui', 'sans-serif'],
        mono:  ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      fontSize: {
        'display-xl': ['48px', { lineHeight: '1.1', fontWeight: '800' }],
        'display-lg': ['32px', { lineHeight: '1.15', fontWeight: '800' }],
        'heading':    ['24px', { lineHeight: '1.3', fontWeight: '700' }],
        'subheading': ['18px', { lineHeight: '1.4', fontWeight: '700' }],
        'body':       ['14px', { lineHeight: '1.6', fontWeight: '400' }],
        'label':      ['11px', { lineHeight: '1.4', fontWeight: '600' }],
        'label-sm':   ['9px',  { lineHeight: '1.3', fontWeight: '600' }],
        'mono-lg':    ['14px', { lineHeight: '1.4', fontWeight: '700' }],
        'mono-sm':    ['10px', { lineHeight: '1.3', fontWeight: '700' }],
      },
      boxShadow: {
        card:    '0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)',
        float:   '0 10px 40px -10px rgba(0,0,0,0.12)',
        glass:   '0 1px 0 rgba(255,255,255,0.05) inset, 0 20px 50px -15px rgba(0,0,0,0.4)',
        accent:  '0 0 20px rgba(44, 154, 166, 0.15)',
      },
      borderRadius: {
        DEFAULT: '8px',
      },
      backdropBlur: {
        xs: '2px',
      },
    },
  },
  plugins: [],
}
