const logger = require("../utils/logger.js");
const {
  registerService,
  loginService,
  forgotPasswordService,
  verifyOTPService,
  resetPasswordService,
} = require("../services/auth.service");
const {
  sendErrorResponse,
  sendSuccessResponse,
} = require("../utils/responseHandler.js");

exports.register = async (req, res) => {
  const {
    full_name,
    email_address,
    phone_number,
    password,
    confirm_password,
    restaurant_name,
  } = req.body;
  if (
    !full_name ||
    !email_address ||
    !phone_number ||
    !password ||
    !confirm_password
  ) {
    return sendErrorResponse(400, "Fields are required");
  }

  if (password !== confirm_password) {
    return sendErrorResponse(400, "Passwords do not match");
  }

  try {
    logger.info(`START: Attempting to create an Admin`);

    const admin = await registerService({
      full_name,
      email_address,
      phone_number,
      password,
      restaurant_name,
    });

    if (!admin.success) {
      return sendErrorResponse(res, admin.statusCode, admin.message);
    }

    logger.info(`END: admin Successfully Created`);
    return sendSuccessResponse(
      res,
      admin.statusCode,
      admin.message,
      admin.data
    );
  } catch (error) {
    logger.error(`END: failed to create admin ${error.message}`);
    return sendErrorResponse(res, 500, "Something went wrong");
  }
};

exports.login = async (req, res) => {
  const { email_address, password } = req.body;

  if (!email_address || !password) {
    return sendErrorResponse(res, 400, "Fields are required");
  }

  try {
    logger.info(`START: Attempting to login admin`);
    const admin = await loginService({ email_address, password });

    if (!admin.success) {
      return sendErrorResponse(res, admin.statusCode, admin.message);
    }

    logger.info(`END: Successfully logged In admin`);

    return sendSuccessResponse(
      res,
      admin.statusCode,
      admin.message,
      admin.data
    );
  } catch (error) {
    logger.error(`END: Failed to login admin ${error.message}`);
    return sendErrorResponse(res, 500, "Something went wrong");
  }
};

exports.forgotPassword = async (req, res) => {
  const { email_address } = req.body;
  if (!email_address) {
    return sendErrorResponse(res,400, "Please Enter an Email address");
  }

  try {
    logger.info(`START: GENERATING OTP FOR ${email_address}`);
    const forgot = await forgotPasswordService({email_address});

    if (!forgot) {
      return sendErrorResponse(
        res,
        forgot.statusCode,
        forgot.message,
      );
    }
    logger.info(`OTP sent to ${email_address}`);
    return sendSuccessResponse(res, forgot.statusCode, forgot.message, forgot.data);
  } catch (error) {
    logger.error(`END: FAILED TO SEND OTP TO ${email_address}`);
    return sendErrorResponse(res, 500, error.message || "Something Went Wrong");
  }
};

exports.verifyotp = async (req, res) => {
  const { otp } = req.body;
  const { email_address } = req;

  if (!otp) {
    return sendErrorResponse(
      400,
      "Enter The OTP sent to your email_address for Change of Password"
    );
  }
  try {
    logger.info(`START: STARTED OTP VERIFICATION FOR ${email_address}`);
    const OTP = await verifyOTPService(email_address,otp);
    if (!OTP) {
      return sendErrorResponse(res, OTP.statusCode, OTP.message);
    }

    return sendSuccessResponse(res, OTP.statusCode, OTP.message, OTP.data);
  } catch (error) {
    logger.error(`END: ${error.message}`);
    return sendErrorResponse(res, 500, error.message);
  }
};

exports.resetPassword = async (req, res) => {
  const { password, confirm_password } = req.body;
  const { email_address } = req.user;

  if (!password && !confirm_password) {
    return sendErrorResponse(res, 400, "Please Enter a New Valid Password");
  }
  try {
    logger.info(`START: STARTED PASSWORD RESET FOR ${email_address}`);
    const reset = await resetPasswordService(email_address , password, confirm_password);
    if (!reset) {
      logger.info(`END:PASSWORD RESET FAILED FOR ${email_address}`);
      return sendErrorResponse(res, reset.statusCode, reset.message);
    }
    logger.info(`PASSWORD RESET SUCCESSFUL FOR ${email_address}`);
    return sendSuccessResponse(
      res,
      reset.statusCode,
      reset.message,
      reset.data
    );
  } catch (error) {
    logger.error(`END:${error.message}`);
    return sendErrorResponse(res, 500, error.message);
  }
};
