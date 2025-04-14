const { rateLimit } = require("express-rate-limit");

const limiter = rateLimit({
    max: 100,
    windowMs: 10 * 60 * 1000, // 10 minutes
    message: `Maximum Requests has been excedeed, try again in 10 minutes!`
})

module.exports = limiter;