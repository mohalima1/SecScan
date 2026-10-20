import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "node:path";

export default defineConfig({
  server: {
    host: "127.0.0.1", port: 8080, strictPort: true,
    proxy: { "/api": { target: "http://127.0.0.1:5000", changeOrigin: true } },
  },
  plugins: [react()],
  resolve: { alias: { "@": path.resolve(__dirname, "./src") } },
});
