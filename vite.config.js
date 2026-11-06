import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Le preview proxifie l'app derrière un hôte du type 3000-<sandbox>.<domaine>.
// On autorise ce domaine uniquement quand il est fourni par la plateforme.
const sandboxDomain = process.env.BASE44_SANDBOX_HOST_DOMAIN

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    strictPort: true,
    allowedHosts: sandboxDomain ? [`.${sandboxDomain}`] : undefined,
    proxy: {
      '/api': {
        target: process.env.API_PROXY_TARGET || 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
