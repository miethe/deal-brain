FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json pnpm-lock.yaml* .npmrc* ./
COPY pnpm-workspace.yaml ./
COPY apps/web/package.json ./apps/web/package.json
COPY packages/js-ui/package.json ./packages/js-ui/package.json
RUN corepack enable pnpm \
    && pnpm install --frozen-lockfile=false

FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY --from=deps /app/pnpm-lock.yaml* ./
COPY pnpm-workspace.yaml ./
COPY package.json ./
COPY apps ./apps
COPY packages ./packages
RUN corepack enable pnpm \
    && pnpm --filter web build

FROM node:20-alpine AS runtime
ENV NODE_ENV=production
WORKDIR /app
RUN corepack enable pnpm
COPY --from=builder /app/apps/web/.next ./apps/web/.next
COPY --from=builder /app/apps/web/package.json ./apps/web/package.json
COPY --from=builder /app/node_modules ./node_modules
EXPOSE 3000
CMD ["pnpm", "--filter", "web", "start"]
