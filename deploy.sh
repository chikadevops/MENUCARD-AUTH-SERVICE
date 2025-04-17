#! /bin/bash

# Install Dependencies
npm ci

# Install Jest
npm install --save-dev jest

# Run Tests
npm test

# Run App
npm run dev