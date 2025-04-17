#! /bin/bash

cd MENUCARD-AUTH-SERVICE

> menucard@1.0.0 dev
> cross-env NODE_ENV=development nodemon index.js

sh: 1: cross-env: not found

# Install Dependencies
npm ci

# Install Jest
npm install --save-dev jest

# Run Tests
npm test

# Run App
npm run dev