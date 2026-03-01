FROM node:22-slim

RUN corepack enable

WORKDIR /app

# Copy package files and install deps (cached layer)
COPY munnir-ui/package.json munnir-ui/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

# Copy config files
COPY munnir-ui/angular.json munnir-ui/tsconfig*.json munnir-ui/proxy.conf.json munnir-ui/.postcssrc.json ./

# Copy source (will be overridden by volume mount in dev)
COPY munnir-ui/src src/
COPY munnir-ui/public public/

EXPOSE 4200

CMD ["pnpm", "ng", "serve", "--host", "0.0.0.0", "--poll", "2000"]
