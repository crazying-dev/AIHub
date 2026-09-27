import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

// 后端 Flask 服务地址（main.py 中监听 127.0.0.1:2685）
const BACKEND = process.env.AIHUB_BACKEND ?? 'http://127.0.0.1:2685'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      // /api/sign*、/api/key* -> Flask
      '/api': { target: BACKEND, changeOrigin: true },
      // /v1/chat/completions 等 OpenAI 兼容接口
      '/v1': { target: BACKEND, changeOrigin: true },
    },
  },
})
