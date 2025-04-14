# Use official Node.js LTS image
FROM node:18-alpine

# Set working directory in container
WORKDIR /app

# Copy package files first (for caching layers)
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy rest of the app
COPY . .

# Expose the port your app runs on (from index.js: 8080)
EXPOSE 8080

# Start the app
CMD ["npm", "run", "dev"]
