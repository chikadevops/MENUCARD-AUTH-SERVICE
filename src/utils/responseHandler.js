const successResponse = (statusCode, message, data) => ({
  statusCode,
  success: true,
  message,
  data,
});

const errorResponse = (statusCode, message) => ({
  statusCode,
  success: false,
  message,
});

const sendSuccessResponse = (res, statusCode, message, data) =>
  res.status(statusCode).json({
    success: true,
    message,
    data,
  });

const sendErrorResponse = (res, statusCode, message) =>
  res.status(statusCode).json({
    success: false,
    message,
  });

module.exports = {
  errorResponse,
  successResponse,
  sendErrorResponse,
  sendSuccessResponse,
};
