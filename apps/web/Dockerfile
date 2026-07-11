# Stage 1: Build Next.js app
FROM node:20-alpine AS builder
RUN corepack enable && corepack prepare pnpm@9.15.4 --activate
WORKDIR /app
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml ./
COPY apps/web/package.json ./apps/web/
# Copy source code
COPY apps/web/ ./apps/web/
# Install dependencies
RUN pnpm install --frozen-lockfile
# Build Next.js app
WORKDIR /app/apps/web
RUN pnpm run build

# Stage 2: Runtime image
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV HOSTNAME="0.0.0.0"
RUN corepack enable && corepack prepare pnpm@9.15.4 --activate
RUN addgroup -g 1001 -S node-group && adduser -u 1001 -S node-user -G node-group
COPY --from=builder /app /app
USER node-user
EXPOSE 3000
CMD ["pnpm", "--filter", "web", "start"]
