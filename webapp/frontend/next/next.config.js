/** @type {import('next').NextConfig} */
module.exports = {
  reactStrictMode: true,
  // 同一originなので /api/* はNginxが直接backendへ振り分ける（rewriteは不要）
};
