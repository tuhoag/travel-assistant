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

# NEXT_PUBLIC_* vars are inlined into the client bundle at build time, so they
# must arrive as build ARGs here — setting them only at container runtime (as
# the dev target's docker-compose environment: block does) has no
# effect on this stage's output.
ARG AGENT_URL
ARG AGENT_ID
ENV AGENT_URL=$AGENT_URL
ENV AGENT_ID=$AGENT_ID

COPY . .
RUN pnpm build

# ---- runner: minimal prod image (default target — used for deployment) ----
FROM node:22-slim AS prod

WORKDIR /app

ENV NODE_ENV=prod

COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE 3000

CMD ["node", "server.js"]
