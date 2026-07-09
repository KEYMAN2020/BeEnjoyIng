import { defineConfig } from "vite"
import vue from "@vitejs/plugin-vue"
import { resolve } from "path"

export default defineConfig({
  plugins: [vue()],
  base: "/app/",
  resolve: {
    alias: { "@": resolve(__dirname, "src") }
  },
  server: {
    port: 5173,
    proxy: {
      "/api": { target: "http://127.0.0.1:5000", changeOrigin: true }
    }
  },
  build: {
    outDir: "../backend/backend/frontend_dist",
    emptyOutDir: true
  }
})
