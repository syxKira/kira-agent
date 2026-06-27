/// <reference types="vitest" />

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

import { createApiProxyConfig } from "./vite.proxy";

declare const process: { env: Record<string, string | undefined> };

const defaultProjectRoot = process.env.VITE_KIRA_PROJECT_ROOT ?? decodeURIComponent(new URL("..", import.meta.url).pathname).replace(/\/$/, "");

export default defineConfig({
  plugins: [react()],
  define: {
    "import.meta.env.VITE_KIRA_PROJECT_ROOT": JSON.stringify(defaultProjectRoot),
  },
  server: {
    port: 5173,
    proxy: createApiProxyConfig(process.env),
  },
  test: {
    environment: "jsdom",
  },
});
