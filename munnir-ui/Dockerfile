FROM node:20-slim

WORKDIR /app

# Copy package files and install deps (cached layer)
COPY munnir-ui/package.json munnir-ui/package-lock.json ./
RUN npm ci

# Copy config files
COPY munnir-ui/angular.json munnir-ui/tsconfig*.json munnir-ui/proxy.conf.json munnir-ui/.postcssrc.json ./

# Copy source (will be overridden by volume mount in dev)
COPY munnir-ui/src src/
COPY munnir-ui/public public/

EXPOSE 4200

CMD ["npx", "ng", "serve", "--host", "0.0.0.0", "--poll", "2000"]
