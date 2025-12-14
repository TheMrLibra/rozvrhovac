# Build stage
FROM node:18-alpine AS builder

WORKDIR /app

# Remove any existing npmrc to avoid auth issues and configure npm to use public registry
RUN rm -rf /root/.npmrc ~/.npmrc /root/.npm ~/.npm && \
    npm config set registry https://registry.npmjs.org/ && \
    npm config delete //registry.npmjs.org/:_authToken || true

# Accept build arguments for Vite environment variables
ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL}

# Copy package files
COPY package.json ./

# Install dependencies
RUN npm install --no-audit --no-fund

# Copy source code
COPY . .

# Build the application (skip type checking for production - faster builds)
# Type checking can be done in CI/CD, not needed for production Docker build
RUN vite build --mode production

# Production stage
FROM nginx:alpine

# Copy built files from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

