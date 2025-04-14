const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const logger = require('./logger');

exports.hashPassword = async (password) => {
  const saltRounds = 10;
  return await bcrypt.hash(password, saltRounds);
};

exports.verifyPassword = async (pass1, pass2) => {
  return await bcrypt.compare(pass1, pass2);
};

exports.generateToken = (adminId) =>
  jwt.sign({ adminId }, process.env.JWT_TOKEN_SECRET, {
    expiresIn: process.env.JWT_TOKEN_LIFETIME,
  });

exports.verifyAccessToken = (token) =>{
  try {
      return jwt.verify(token, process.env.JWT_TOKEN_SECRET)
  } catch (error) {
      logger.error(`Invalid Access token: ${error.message}`)
      return false
  }
}

