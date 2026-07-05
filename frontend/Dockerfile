# VITE_API_BASE_URL is baked in at build time (Vite env vars are static,
# resolved when the bundle is built) -- pass it as a build arg so the
# published image points at whatever backend URL the deployer needs.
ARG VITE_API_BASE_URL=http://localhost:8000

FROM node:20-alpine AS builder
WORKDIR /build
COPY package.json package-lock.json* ./
# npm ci is avoided here: @tailwindcss/oxide's optional WASM fallback
# (@tailwindcss/oxide-wasm32-wasi, pulling in @emnapi/core/@emnapi/runtime)
# resolves to slightly different versions across npm install runs, which
# repeatedly makes npm ci reject an otherwise-fine lock file as "out of
# sync." npm install tolerates that drift and still respects the lock
# file's pinned versions for everything else.
RUN npm install
COPY . .
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

FROM nginx:1.27-alpine AS runtime
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /build/dist /usr/share/nginx/html

EXPOSE 80
HEALTHCHECK --interval=30s --timeout=3s CMD wget -qO- http://localhost:80/ || exit 1
