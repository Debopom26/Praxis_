import { defineConfig as defineViteConfig } from "vite";
import { defineConfig as defineLovableConfig } from "@lovable.dev/vite-tanstack-config";
import { cloudflare } from "@cloudflare/vite-plugin";

export default defineViteConfig(async (env) => {
  const config = await defineLovableConfig({
    tanstackStart: {
      server: { entry: "server" },
    },
  })(env);

  config.plugins = [
    cloudflare({ viteEnvironment: { name: "ssr" } }),
    ...(config.plugins ?? []),
  ];

  return config;
});