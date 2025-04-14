const jwt = require("jsonwebtoken");
const Otp = require("../models/otp.model");
const logger = require("../utils/logger");

exports.verifyResetToken = (req, res, next) => {
  const authHeader = req.headers["authorization"];
  const token = authHeader && authHeader.split(" ")[1];

  if (!token) {
    return res.status(401).json({
      success: false,
      message: "No token provided",
    });
  }

  jwt.verify(token, process.env.JWT_SECRET, (err, decoded) => {
    if (err) {
      return res.status(401).json({
        success: false,
        message: "Invalid/expired token",
      });
    }
    req.user = { email_address: decoded.email_address };
    next();
  });
};

exports.getEmailFromOTP = async (req, res, next) => {
  const { otp } = req.body;

  try {
    const otpRecord = await Otp.findOne({ otp });
    if (!otpRecord) {
      return res.status(400).json({
        success: false,
        message: "Invalid OTP",
      });
    }

    req.email_address = otpRecord.email_address;
    next();
  } catch (error) {
    logger.error(`Error fetching email from OTP: ${error.message}`);
    return res.status(500).json({
      success: false,
      message: "OTP verification failed",
    });
  }
};
