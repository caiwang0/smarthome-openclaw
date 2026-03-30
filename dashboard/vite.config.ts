import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      "/api": `http://localhost:${process.env.VITE_API_PORT || "3001"}`,
    },
  },
});
