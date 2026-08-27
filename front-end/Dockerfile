# ---- deps: shared base with dependencies installed ----
FROM node:22-slim AS deps

WORKDIR /app

RUN corepack enable

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile

# ---- development: used by docker-compose for local development (hot reload) ----
FROM deps AS development

COPY . .

EXPOSE 3000

CMD ["pnpm", "dev"]

# ---- builder: compiles the production build ----
FROM deps AS builder

COPY . .
RUN pnpm build

# ---- runner: minimal production image (default target — used for deployment) ----
FROM node:22-slim AS runner

WORKDIR /app

ENV NODE_ENV=production

COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE 3000

CMD ["node", "server.js"]
