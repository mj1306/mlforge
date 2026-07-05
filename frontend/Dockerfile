# VITE_API_BASE_URL is baked in at build time (Vite env vars are static,
# resolved when the bundle is built) -- pass it as a build arg so the
# published image points at whatever backend URL the deployer needs.
ARG VITE_API_BASE_URL=http://localhost:8000

FROM node:20-alpine AS builder
WORKDIR /build
COPY package.json package-lock.json* ./
RUN npm ci
COPY . .
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

FROM nginx:1.27-alpine AS runtime
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /build/dist /usr/share/nginx/html

EXPOSE 80
HEALTHCHECK --interval=30s --timeout=3s CMD wget -qO- http://localhost:80/ || exit 1
