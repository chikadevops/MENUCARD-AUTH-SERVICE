#! /bin/bash 

# Install Dependencies
npm ci

# Install Jest
npm install --save-dev jest

# Run Tests
npm test

# Run App
npm run dev &
DEV_PID=$!
sleep 30
kill -SIGINT $DEV_PID
echo "Stopped dev server after timeouts"
