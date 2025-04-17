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
echo "Dev server running with PID $DEV_PID"
sleep 60
kill -- -$DEV_PID
echo "Dev server stopped after 1 minute"
