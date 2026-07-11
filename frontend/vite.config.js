import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Forward /submit-code to the FastAPI backend
      '/submit-code': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
