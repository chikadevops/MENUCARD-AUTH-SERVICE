#! /bin/bash 

# Install Dependencies
npm ci

# Install Jest
npm install --save-dev jest

# Run Tests
npm test

# Run App
timeout --foreground 60s npm run dev || echo "Stopped dev server after timeout"