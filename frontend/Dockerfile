# Stage 1: Build production bundle
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependency manifests
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci || npm install

# Copy source code and build
COPY frontend/ ./
RUN npm run build

# Stage 2: Production Nginx Server
FROM nginx:alpine

# Copy custom Nginx configuration
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Copy build artifacts from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
