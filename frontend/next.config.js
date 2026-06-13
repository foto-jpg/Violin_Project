/** @type {import('next').NextConfig} */
// HF build = static export (served by FastAPI). Local = standalone server with the
// runtime proxy Route Handler at app/api/backend/[...path]/route.ts.
// NOTE: the HF Dockerfile removes app/api before building - static export can't host
// the dynamic proxy route, and on HF the API is same-origin via FastAPI.
const isHF = process.env.NEXT_PUBLIC_HF === '1'

const nextConfig = isHF
  ? {
      output: 'export',
      trailingSlash: true,
      images: { unoptimized: true },
    }
  : {
      output: 'standalone',
    }

module.exports = nextConfig
