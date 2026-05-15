/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
        display: ['IBM Plex Mono', 'monospace'],
      },
      colors: {
        terminal: {
          bg:       '#080c0f',
          surface:  '#0d1317',
          border:   '#1a2530',
          muted:    '#1e2d3a',
          text:     '#8ba8bc',
          dim:      '#3d5a6e',
          green:    '#00d4a0',
          red:      '#ff4c6a',
          yellow:   '#f5a623',
          blue:     '#4a9eff',
          white:    '#e8f4f8',
        },
      },
      animation: {
        'pulse-green': 'pulseGreen 0.4s ease-out',
        'pulse-red':   'pulseRed 0.4s ease-out',
        'blink':       'blink 1s step-end infinite',
      },
      keyframes: {
        pulseGreen: {
          '0%':   { color: '#00d4a0', textShadow: '0 0 8px #00d4a0' },
          '100%': { color: 'inherit', textShadow: 'none' },
        },
        pulseRed: {
          '0%':   { color: '#ff4c6a', textShadow: '0 0 8px #ff4c6a' },
          '100%': { color: 'inherit', textShadow: 'none' },
        },
        blink: {
          '0%, 100%': { opacity: '1' },
          '50%':      { opacity: '0' },
        },
      },
    },
  },
  plugins: [],
}
