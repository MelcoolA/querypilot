import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Hide the "N" dev-tools button so it doesn't appear in demo recordings.
  // Compile and runtime errors are still shown in development.
  devIndicators: false,
};

export default nextConfig;
