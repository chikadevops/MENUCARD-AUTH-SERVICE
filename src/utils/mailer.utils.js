const nodemailer = require('nodemailer');
const logger = require('./logger');
require('dotenv').config();



const transporter = nodemailer.createTransport({
  host: 'smtp.gmail.com',
  port: 465,
  secure: true,
  auth: {
    user: process.env.GMAIL_USER,
    pass: process.env.GMAIL_PASS
  }
});


const sendOTPEmail = async (email_address, otp) => {
  try {
    await transporter.sendMail({
      from: `"Chop Central" <${process.env.GMAIL_USER}>`,
      to: email_address,
      subject: 'Your Password Reset OTP',
      html: `
        <p>Use this OTP to reset your password:</p>
        <h2>${otp}</h2>
        <p><em>Expires in 10 minutes.</em></p>
      `
    });
    logger.info(`OTP email sent to ${email_address}`);
  } catch (error) {
    logger.error(`Email send failed: ${error.message}`);
    throw error;
  }
};

module.exports = { sendOTPEmail };