FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json pnpm-lock.yaml* .npmrc* ./
COPY pnpm-workspace.yaml ./
COPY apps/web/package.json ./apps/web/package.json
COPY packages/js-ui/package.json ./packages/js-ui/package.json
RUN corepack enable pnpm \
    && pnpm install --frozen-lockfile=false

FROM node:20-alpine AS runtime
ENV NODE_ENV=development
WORKDIR /app
RUN corepack enable pnpm
COPY --from=deps /app/node_modules ./node_modules
COPY --from=deps /app/pnpm-lock.yaml* ./
COPY pnpm-workspace.yaml ./
COPY package.json ./
COPY apps ./apps
COPY packages ./packages
EXPOSE 3000
CMD ["pnpm", "--filter", "web", "dev", "--", "-H", "0.0.0.0"]
