const Otp = require("../models/otp.model");
const otpGenerator = require("otp-generator");
const logger = require("../utils/logger");

const generateOTP = async (email_address) => {
  try {
    const otp = otpGenerator.generate(6, {
      upperCaseAlphabets: false,
      specialChars: false,
      digits: true,
      lowerCaseAlphabets: false,
    });

    await Otp.findOneAndUpdate(
      { email_address },
      { otp, isVerified: false, createdAt: new Date() },
      { upsert: true, new: true }
    );

    logger.info(`OTP generated for ${email_address}`);
    return { success: true, otp };
  } catch (error) {
    logger.error(`OTP generation failed: ${error.message}`);
    return { success: false, message: "Failed to generate OTP" };
  }
};

const verifyOTP = async (email_address, otp) => {
  try {
    const record = await Otp.findOneAndUpdate(
      { email_address, otp },
      { $set: { isVerified: true } },
      { new: true }
    );

    if (!record) {
      logger.warn(`Invalid OTP for ${email_address}`);
      return { success: false, message: "Invalid OTP" };
    }

    logger.info(`OTP verified for ${email_address}`);
    return { success: true, message: "OTP verified successfully" };
  } catch (error) {
    logger.error(`OTP verification failed: ${error.message}`);
    return { success: false, message: "OTP verification failed" };
  }
};

module.exports = { generateOTP, verifyOTP };
