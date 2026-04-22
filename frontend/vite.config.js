import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {

        target: 'https://go-retail-moderno.onrender.com/api/v1',
        changeOrigin: true,
      },
    },
  },
})
