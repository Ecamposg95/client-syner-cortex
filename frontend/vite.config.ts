import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // Pre-bundle heavy charting deps at startup so the first navigation to a chart
  // view doesn't trigger a mid-session re-optimize + full reload (blank page).
  optimizeDeps: {
    include: ['recharts'],
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
})
