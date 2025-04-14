const { register } = require('../../controllers/auth.controller');
const { registerService } = require('../../services/auth.service');
const { sendErrorResponse, sendSuccessResponse } = require('../../utils/responseHandler');
const logger = require('../../utils/logger');

jest.mock('../../services/auth.service');
jest.mock('../../utils/responseHandler');
jest.mock('../../utils/logger');

describe('Auth Controller - Register', () => {
    let mockReq;
    let mockRes;

    beforeEach(() => {
        mockReq = {
            body: {
                full_name: 'Test User',
                email_address: 'test@test.com',
                phone_number: '1234567890',
                password: 'password123',
                confirm_password: 'password123',
                restaurant_name: 'Test Restaurant'
            }
        };
        mockRes = {};
        sendErrorResponse.mockClear();
        sendSuccessResponse.mockClear();
        registerService.mockClear();
    });

    test('should return error if required fields are missing', async () => {
        mockReq.body.full_name = '';
        await register(mockReq, mockRes);
        expect(sendErrorResponse).toHaveBeenCalledWith(400, 'Fields are required');
    });

    test('should return error if passwords do not match', async () => {
        mockReq.body.confirm_password = 'different';
        await register(mockReq, mockRes);
        expect(sendErrorResponse).toHaveBeenCalledWith(400, 'Passwords do not match');
    });

    test('should create admin successfully', async () => {
        const mockAdmin = {
            success: true,
            statusCode: 201,
            message: 'Admin created successfully',
            newAdmin: { id: 1, email: 'test@test.com' }
        };
        registerService.mockResolvedValue(mockAdmin);

        await register(mockReq, mockRes);

        expect(registerService).toHaveBeenCalledWith({
            full_name: mockReq.body.full_name,
            email_address: mockReq.body.email_address,
            phone_number: mockReq.body.phone_number,
            password: mockReq.body.password,
            restaurant_name: mockReq.body.restaurant_name
        });

        expect(sendSuccessResponse).toHaveBeenCalledWith(
            mockRes,
            mockAdmin.statusCode,
            mockAdmin.message,
            mockAdmin.data
        );
    });

    test('should handle registration failure', async () => {
        const mockError = {
            success: false,
            statusCode: 400,
            message: 'Registration failed'
        };
        registerService.mockResolvedValue(mockError);

        await register(mockReq, mockRes);

        expect(sendErrorResponse).toHaveBeenCalledWith(
            mockRes,
            mockError.statusCode,
            mockError.message
        );
    });

    test('should handle unexpected errors', async () => {
        registerService.mockRejectedValue(new Error('Database error'));

        await register(mockReq, mockRes);

        expect(sendErrorResponse).toHaveBeenCalledWith(
            mockRes,
            500,
            'Something went wrong'
        );
    });
});