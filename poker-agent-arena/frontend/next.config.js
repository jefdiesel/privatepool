/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,

  // Webpack configuration for Solana compatibility
  webpack: (config, { isServer }) => {
    if (!isServer) {
      // Polyfills for Solana web3.js in browser
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        os: false,
        path: false,
        crypto: false,
      };
    }

    // Handle ESM modules
    config.externals.push("pino-pretty", "lokijs", "encoding");

    return config;
  },

  // Environment variables exposed to the browser
  env: {
    NEXT_PUBLIC_SOLANA_RPC_URL: process.env.NEXT_PUBLIC_SOLANA_RPC_URL,
    NEXT_PUBLIC_PROGRAM_ID: process.env.NEXT_PUBLIC_PROGRAM_ID,
  },
};

module.exports = nextConfig;
