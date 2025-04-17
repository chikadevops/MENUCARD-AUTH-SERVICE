#! /bin/bash 

# Install Dependencies
npm ci

# Install Jest
npm install --save-dev jest

# Run Tests
npm test

# Run App
timeout 60 npm run dev || echo "Dev server stopped after 1 minute"
