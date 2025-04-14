const express = require('express');
 const {forgotPassword,resetPassword,verifyotp } = require('../controllers/auth.controller');
const { getEmailFromOTP } = require('../middlewares/otp.validation');
const { verifyResetToken } = require('../middlewares/otp.validation'); 
const router = express.Router();
const { schemas, validate } = require('../middlewares/auth.validation');
const { register, login } = require('../controllers/auth.controller');
/**
 * @swagger
 * /api/v1/admin/sign-up:
 *   post:
 *     summary: Register a new admin
 *     tags: [Auth]
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - full_name
 *               - email_address
 *               - phone_number
 *               - password
 *               - confirm_password
 *             properties:
 *               full_name:
 *                 type: string
 *                 description: Admin's full name
 *               email_address:
 *                 type: string
 *                 format: email
 *                 description: Admin's email address
 *               phone_number:
 *                 type: string
 *                 description: Admin's phone number
 *               password:
 *                 type: string
 *                 format: password
 *                 description: Admin's password
 *               confirm_password:
 *                 type: string
 *                 format: password
 *                 description: Confirmation of admin's password
 *               restaurant_name:
 *                 type: string
 *                 description: Name of the restaurant
 *     responses:
 *       201:
 *         description: Admin created successfully
 *       400:
 *         description: Validation error
 *       500:
 *         description: Server error
 */
router.post('/sign-up', validate(schemas.register),register);

/**
 * @swagger
 * /api/v1/admin/login:
 *   post:
 *     summary: Login an admin
 *     tags: [Auth]
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - email_address
 *               - password
 *             properties:
 *               email_address:
 *                 type: string
 *                 format: email
 *                 description: Admin's email address
 *               password:
 *                 type: string
 *                 format: password
 *                 description: Admin's password
 *     responses:
 *       200:
 *         description: Login successful
 *       400:
 *         description: Invalid credentials
 *       500:
 *         description: Server error
 */
router.post('/login', validate(schemas.login), login);
/**
 * @swagger
 * /api/v1/admin/forget-password:
 *   post:
 *     summary: Request password reset for admin
 *     tags: [Auth]
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - email_address
 *             properties:
 *               email_address:
 *                 type: string
 *                 format: email
 *                 description: Admin's email address
 *     responses:
 *       200:
 *         description: Password reset link sent successfully
 *       400:
 *         description: Invalid email address or error sending email
 */
router.post('/forget-password', forgotPassword);
/**
 * @swagger
 * /api/v1/admin/verify-otp:
 *   post:
 *     summary: Verify OTP for password reset
 *     tags: [Auth]
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - email_address
 *               - otp_code
 *             properties:
 *               email_address:
 *                 type: string
 *                 format: email
 *                 description: Admin's email address
 *               otp_code:
 *                 type: string
 *                 description: OTP code sent to the admin's email address
 *     responses:
 *       200:
 *         description: OTP verified successfully
 *       400:
 *         description: Invalid OTP or email address
 */
router.post('/verify-otp',getEmailFromOTP, verifyotp);
/**
 * @swagger
 * /api/v1/admin/reset-password:
 *   post:
 *     summary: Reset password for admin
 *     tags: [Auth]
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - email_address
 *               - new_password
 *               - confirm_password
 *             properties:
 *               email_address:
 *                 type: string
 *                 format: email
 *                 description: Admin's email address
 *               new_password:
 *                 type: string
 *                 format: password
 *                 description: New password for the admin
 *               confirm_password:
 *                 type: string
 *                 format: password
 *                 description: Confirmation of the new password
 *     responses:
 *       200:
 *         description: Password reset successfully
 *       400:
 *         description: Validation error or invalid OTP/email address
 */
router.post('/reset-password',verifyResetToken, resetPassword);


module.exports = router;
