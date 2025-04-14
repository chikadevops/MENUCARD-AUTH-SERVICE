const { sendErrorResponse } = require("../utils/responseHandler.js");
const { verifyAccessToken } = require("../utils/auth.utils.js");

const Authenticate = (req, res, next) => {
  const header = req.headers["authorization"];
  if (!header)
    return sendErrorResponse(res, 401, "`Authorization` header is required");
  if (header.startsWith("Bearer ")) {
    const token = header.replace("Bearer ", "");
    try {
      const payload = verifyAccessToken(token);

      if (!payload) return sendErrorResponse(res, 401, "Invalid token");

      req.adminId = payload.adminId;
      next();
    } catch (error) {
      return sendErrorResponse(res, 401, `Failed to authenticate token ${error.message}`);
    }
  }
};

module.exports = { Authenticate };
