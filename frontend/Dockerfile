# ---- deps: shared base with dependencies installed ----
FROM node:22-slim AS deps

WORKDIR /app

RUN corepack enable

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile

# ---- dev: used by docker-compose for local dev (hot reload) ----
FROM deps AS dev

COPY . .

EXPOSE 3000

CMD ["pnpm", "dev"]

# ---- builder: compiles the prod build ----
FROM deps AS builder

COPY . .
RUN pnpm build

# ---- runner: minimal prod image (default target — used for deployment) ----
FROM node:22-slim AS prod

WORKDIR /app

ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE 3000

CMD ["node", "server.js"]
