FROM node:20-alpine

WORKDIR /app

# Copy package manifests first for layer caching
COPY package.json package-lock.json* ./

# Install all dependencies (including devDependencies for hot-reload)
RUN npm install

# Copy application source
COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]
