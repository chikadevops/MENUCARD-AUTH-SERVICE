const mongoose = require('mongoose');

const otpSchema = new mongoose.Schema({
  email_address: {
    type: String,
    required: true,
    index: true
  },
  otp: {
    type: String,
    required: true
  },
  isVerified: {
    type: Boolean,
    default: false
  },
  createdAt: {
    type: Date,
    default: Date.now,
    expires: 600
  }
});

 const Otp= mongoose.model('Otp', otpSchema);
module.exports = Otp;