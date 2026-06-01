import { defineConfig } from 'vite'

export default defineConfig({
  server: {
    port: 5174,
    strictPort: false,
    proxy: {
      '/api': {
        target: 'http://localhost:9000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: '../nginx/static',
    emptyOutDir: true,
  },
})
