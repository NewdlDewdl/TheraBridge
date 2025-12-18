import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Suppress hydration warnings caused by browser extensions (e.g., Dark Reader)
  onError: undefined,
};

export default nextConfig;
