export default defineNuxtConfig({
  compatibilityDate: "2024-11-01",
  devtools: { enabled: false },
  nitro: {
    preset: "node-server",
  },
  // /api/* はNginx経由でbackendに転送される想定
});
