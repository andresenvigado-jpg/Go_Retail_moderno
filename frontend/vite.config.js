import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        //target: 'http://localhost:8000', // Solo dev local  https://go-retail-moderno.onrender.com/api/docs
        target: 'https://go-retail-moderno.onrender.com/api',
        changeOrigin: true,
      },
    },
  },
})
