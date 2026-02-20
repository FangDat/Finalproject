const { defineConfig } = require("@vue/cli-service");

module.exports = defineConfig({
  transpileDependencies: true,

  // ⭐ VERY IMPORTANT FOR VERCEL
  publicPath: "/",

  // tránh lỗi asset path production
  assetsDir: "assets",

  // fix chunk loading + icon lỗi
  filenameHashing: true,
});
