const Admin = require("../models/admin.model.js");
const logger = require("../utils/logger.js");

const jwt = require('jsonwebtoken');
const Otp =require('../models/otp.model')
const { generateOTP, verifyOTP } = require('../services/otp.service');
const { sendOTPEmail } = require('../utils/mailer.utils');

const {
  hashPassword,
  verifyPassword,
  generateToken,
} = require("../utils/auth.utils.js");

const {
  successResponse,
  errorResponse,
} = require("../utils/responseHandler.js");

exports.registerService = async ({
  full_name,
  email_address,
  phone_number,
  restaurant_name,
  password,
}) => {
  try {
    logger.info(`START: Running Register Service`);
    const adminExist = await Admin.findOne({ email_address });
    if (adminExist) {
      return errorResponse(400, "email address already exist");
    }

    const password_hash = await hashPassword(password);

    const newAdmin = await Admin.create({
      full_name,
      email_address,
      phone_number,
      restaurant_name,
      passwordHash: password_hash,
    });

    logger.info(`END: Register Service reached`);
    return successResponse(201, "Admin created Successfully", newAdmin);
  } catch (error) {
    logger.error(`END: Failed to create an admin: ${error.message}`);
    return errorResponse(500, `Internal Server Error`);
  }
};

exports.loginService = async ({ email_address, password }) => {
  try {
    logger.info("START: Running Login Service");
    const admin = await Admin.findOne({ email_address });

    if (!admin) {
      return errorResponse(400, "Invalid email address or password");
    }

    // confirm hashed password
    const adminPassword = admin.passwordHash;
    const isMatch = await verifyPassword(password, adminPassword);

    if (!isMatch) {
      return errorResponse(400, "Invalid email address or password");
    }

    const token = generateToken(admin._id);

    logger.info("END: Login Service Completed");
    return successResponse(200, "Admin Login Successfully", { admin, token });
  } catch (error) {
    logger.error(`END: Failed to login admin: ${error.message}`);
    return errorResponse(500, "Something Went Wrong");
  }
};

exports.forgotPasswordService = async ({ email_address }) => {

  try {
    logger.info(`START: Password reset requested for ${email_address}`);

    const admin = await Admin.findOne({ email_address });
    if (!admin) {
      logger.warn(`Admin not found: ${email_address}`);
      return errorResponse(400,
      "Admin Not Found"
      );
    }

    const { success, otp, message } = await generateOTP(email_address);
    if (!success) {
      return errorResponse(400, message);
    }

    await sendOTPEmail(email_address, otp);

    logger.info(`END: OTP sent to ${email_address}`);
    return successResponse(200, "OTP sent successfully", 
    );
  } catch (error) {
    logger.error(`END: Password reset failed: ${error.message}`);
    return errorResponse(500, "Password reset failed");
  }
};

exports.verifyOTPService = async (email_address, otp ) => {
 

  try {
    logger.info(`START: OTP verification for ${email_address}`);

    const messages = await verifyOTP(email_address, otp);
    if (!messages.success) {
      return errorResponse(400, messages.message);
    }
    const resetToken = jwt.sign(
      { email_address }, 
      process.env.JWT_SECRET, 
      { expiresIn: '10m' } 
    );
    
    logger.info(`END: OTP verified for ${email_address}`);
    return successResponse(200, "OTP verified successfully", { resetToken });
  } catch (error) {
    logger.error(`END: OTP verification failed: ${error.message}`);
    return errorResponse(500, "OTP verification failed");
  }
};

exports.resetPasswordService = async (email_address, password, confirm_password ) => {


  try {
    logger.info(`START: Password reset for ${email_address}`);

   
    if (password !== confirm_password) {
      logger.warn('Password mismatch during reset');
      return errorResponse(400, "Passwords do not match");
    }

    const otpRecord = await Otp.findOne({ 
      email_address, 
      isVerified: true 
    });

    if (!otpRecord) {
      logger.warn(`Unverified OTP attempt for ${email_address}`);
      return errorResponse(403, "Invalid or expired OTP");
    }

   
    const hashedPassword = await hashPassword(password);
     await Admin.findOneAndUpdate({email_address},{passwordHash:hashedPassword},{new:true});

   
    await Otp.deleteOne({ email_address });

    logger.info(`END: Password reset successful for ${email_address}`);
    return successResponse(200, "Password reset successfully", null);
  } catch (error) {
    logger.error(`END: Password reset failed: ${error.message}`);
    return errorResponse(500, "Password reset failed");
  }
};
