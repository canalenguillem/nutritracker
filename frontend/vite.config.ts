import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

const DEFAULT_DEVELOPMENT_PORT = 5173;
const DEFAULT_PREVIEW_PORT = 4173;
const DEFAULT_APP_NAME = "NutriTrack AI";

const parsePort = (value: string | undefined, fallback: number): number => {
  const parsedValue = Number(value);

  return Number.isInteger(parsedValue) && parsedValue > 0 ? parsedValue : fallback;
};

/** Hosts the dev server answers to, beyond localhost and plain IP addresses. */
const parseAllowedHosts = (value: string | undefined): string[] =>
  (value ?? "")
    .split(",")
    .map((host) => host.trim())
    .filter(Boolean);

const escapeHtml = (value: string): string =>
  value.replace(
    /[&<>'"]/g,
    (character) =>
      ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        "'": "&#39;",
        '"': "&quot;",
      })[character] ?? character,
  );

export default defineConfig(({ mode }) => {
  const environment = loadEnv(mode, ".", "");
  const appName = environment.VITE_APP_NAME?.trim() || DEFAULT_APP_NAME;

  return {
    plugins: [
      react(),
      {
        name: "inject-app-name",
        transformIndexHtml: (html) => html.replaceAll("__APP_NAME__", escapeHtml(appName)),
      },
    ],
    server: {
      host: "0.0.0.0",
      port: parsePort(environment.VITE_DEV_SERVER_PORT, DEFAULT_DEVELOPMENT_PORT),
      strictPort: true,
      allowedHosts: parseAllowedHosts(environment.VITE_DEV_ALLOWED_HOSTS),
      proxy: {
        "/api": {
          target: environment.VITE_API_PROXY_TARGET || "http://backend:8000",
          changeOrigin: true,
        },
      },
    },
    preview: {
      host: "0.0.0.0",
      port: parsePort(environment.VITE_PREVIEW_PORT, DEFAULT_PREVIEW_PORT),
      strictPort: true,
    },
    build: {
      outDir: "dist",
      sourcemap: false,
    },
  };
});
