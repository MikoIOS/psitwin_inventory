import { fileURLToPath, URL } from 'node:url'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  // En desarrollo el navegador llama a /api/v1 (mismo origen) y Vite lo reenvía al backend: evita CORS.
  const proxyTarget = env.VITE_PROXY_TARGET || 'http://localhost:8000'
  return {
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 5173,
    // ws: true → también reenvía el WebSocket de monitoreo (/api/v1/ws/monitoreo).
    proxy: { '/api': { target: proxyTarget, changeOrigin: true, ws: true } },
  },
  preview: {
    proxy: { '/api': { target: proxyTarget, changeOrigin: true, ws: true } },
  },
  build: {
    rolldownOptions: {
      output: {
        codeSplitting: {
          groups: [
            { name: 'vendor-react', test: /node_modules[\\/](react|react-dom|scheduler)[\\/]/ },
            { name: 'vendor-router', test: /node_modules[\\/]react-router[\\/]/ },
            { name: 'vendor-query', test: /node_modules[\\/]@tanstack[\\/]/ },
            { name: 'vendor-forms', test: /node_modules[\\/](react-hook-form|@hookform|zod)[\\/]/ },
          ],
        },
      },
    },
  },
}
})
