const request = require('supertest');
const {app} = require('../../app');
const Admin = require('../../models/admin.model');
const Otp = require('../../models/otp.model');
const { generateOTP, verifyOTP } = require('../../services/otp.service');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const logger = require('../../utils/logger');
const mongoose = require('mongoose');

jest.mock('../models/admin.model');
jest.mock('../models/otp.model');
jest.mock('../services/otp.service');
jest.mock('bcryptjs');
jest.mock('jsonwebtoken');
jest.mock('../utils/logger');

// Mock middleware to set req.user
app.use((req, res, next) => {
  req.user = { email_address: 'test@test.com' };
  next();
});


describe('Auth Endpoints', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    describe('POST /api/v1/admin/forget-password', () => {
        it('should send OTP when email exists', async () => {
            Admin.findOne.mockResolvedValue({
                email_address: 'test@test.com'
            });

            generateOTP.mockResolvedValue({
                success: true,
                otp: '123456',
                message: 'OTP generated'
            });

            const res = await request(app)
                .post('/api/v1/admin/forget-password')
                .send({ email_address: 'test@test.com' });

            expect(res.statusCode).toBe(200);
            expect(res.body.success).toBe(true);
            expect(res.body.message).toBe('OTP sent to email');
        });

        it('should return error if email does not exist', async () => {
            Admin.findOne.mockResolvedValue(null);

            const res = await request(app)
                .post('/api/v1/admin/forget-password')
                .send({ email_address: 'nonexistent@test.com' });

            expect(res.statusCode).toBe(404);
            expect(res.body.message).toBe('Admin not found');
        });
    });


    describe('POST /api/v1/admin/verify-otp', () => {
        it('should return reset token on successful OTP verification', async () => {
          Otp.findOne = jest.fn().mockResolvedValue(null);
            verifyOTP.mockResolvedValue({
                success: true,
                message: 'OTP verified'
            });

            jwt.sign.mockReturnValue('mockedResetToken');

            const res = await request(app)
                .post('/api/v1/admin/verify-otp')
                .send({ email_address: 'test@test.com', otp: '123456' });

            expect(res.statusCode).toBe(200);
            expect(res.body.success).toBe(true);
            expect(res.body.resetToken).toBe('mockedResetToken');
        });

        it('should return error if OTP is invalid', async () => {
            verifyOTP.mockResolvedValue({ success: false, message: 'Invalid OTP' });

            const res = await request(app)
                .post('/api/v1/admin/verify-otp')
                .send({ email_address: 'test@test.com', otp: '000000' });

            expect(res.statusCode).toBe(400);
            expect(res.body.message).toBe('Invalid OTP');
        });
    });

    describe('POST /api/v1/admin/reset-password', () => {
        it('should reset password when OTP is verified', async () => {
            Otp.findOne.mockResolvedValue({
                email_address: 'test@test.com',
                isVerified: true
            });

            bcrypt.hash.mockResolvedValue('hashedPassword123');
            Admin.updateOne.mockResolvedValue({ acknowledged: true, modifiedCount: 1 });
            Otp.deleteOne.mockResolvedValue({ acknowledged: true, deletedCount: 1 });

            const res = await request(app)
                .post('/api/v1/admin/reset-password')
                .send({ password: 'newPass123', confirm_password: 'newPass123' })
                .set('Authorization', 'Bearer validToken');

            expect(res.statusCode).toBe(200);
            expect(res.body.message).toBe('Password updated successfully');
        });

        it('should return error if passwords do not match', async () => {
            const res = await request(app)
                .post('/api/v1/admin/reset-password')
                .send({ password: 'newPass123', confirm_password: 'wrongPass123' })
                .set('Authorization', 'Bearer validToken');

            expect(res.statusCode).toBe(400);
            expect(res.body.message).toBe('Passwords do not match');
        });

        it('should return error if user is not found', async () => {
            Otp.findOne.mockResolvedValue(null);

            const res = await request(app)
                .post('/api/v1/admin/reset-password')
                .send({ password: 'newPass123', confirm_password: 'newPass123' })
                .set('Authorization', 'Bearer validToken');

            expect(res.statusCode).toBe(403);
            expect(res.body.message).toBe("OTP not verified. Request a new one.");
        });
    });
});
