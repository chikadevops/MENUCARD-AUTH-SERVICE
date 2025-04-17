#! /bin/bash

# Clone or update repo
if [ -d "MENUCARD-AUTH-SERVICE" ]; then
    cd MENUCARD-AUTH-SERVICE && git pull
else
    git clone https://github.com/chikadevops/MENUCARD-AUTH-SERVICE.git
    cd MENUCARD-AUTH-SERVICE
fi

# Install Dependencies
npm ci

# Install Jest
npm install --save-dev jest

# Run Tests
npm test

# Run App
npm run dev