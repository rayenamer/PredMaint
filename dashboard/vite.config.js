import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Calls to /api/* are forwarded to the FastAPI service (no CORS needed)
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});
