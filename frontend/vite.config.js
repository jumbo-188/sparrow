import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      // 本地开发时，将 /api 请求转发到 NAS 后端
      '/api': {
        target: 'http://192.168.0.105:5080', // 替换为你 NAS 的实际 IP
        changeOrigin: true,
        secure: false,
      }
    }
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    emptyOutDir: true
  }
})