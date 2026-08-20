// vite.config.js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src')
    }
  },
  server: {
    port: 3000,
    proxy: {
      // ✅ 代理 /api 请求到后端
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      // ✅ 代理 /output 请求到后端（图片访问）
      '/output': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      // ✅ 代理 /data 请求到后端（上传的图片访问）
      '/data': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  css: {
    preprocessorOptions: {
      scss: {
        additionalData: `@use "@/styles/variables.scss" as *;`
      }
    }
  }
})