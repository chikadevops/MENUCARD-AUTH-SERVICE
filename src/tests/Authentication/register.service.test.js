const { registerService } = require('../../services/auth.service');
const Admin = require('../../models/admin.model');
const { hashPassword } = require('../../utils/auth.utils');
const logger = require('../../utils/logger');

jest.mock('../../models/admin.model');
jest.mock('../../utils/auth.utils');
jest.mock('../../utils/logger');

describe('Auth Service - Register', () => {
    const mockAdminData = {
        full_name: 'Test Admin',
        email_address: 'test@test.com',
        phone_number: '1234567890',
        restaurant_name: 'Test Restaurant',
        password: 'testpass123'
    };

    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('should register a new admin successfully', async () => {
        const hashedPassword = 'hashedPassword123';
        const newAdmin = {
            ...mockAdminData,
            passwordHash: hashedPassword,
            _id: 'someId123'
        };

        Admin.findOne.mockResolvedValue(null);
        hashPassword.mockResolvedValue(hashedPassword);
        Admin.create.mockResolvedValue(newAdmin);

        const result = await registerService(mockAdminData);

        expect(Admin.findOne).toHaveBeenCalledWith({ email_address: mockAdminData.email_address });
        expect(hashPassword).toHaveBeenCalledWith(mockAdminData.password);
        expect(Admin.create).toHaveBeenCalledWith({
            full_name: mockAdminData.full_name,
            email_address: mockAdminData.email_address,
            phone_number: mockAdminData.phone_number,
            restaurant_name: mockAdminData.restaurant_name,
            passwordHash: hashedPassword
        });
        expect(result.statusCode).toBe(201);
        expect(result.message).toBe('Admin created Successfully');
        expect(result.data).toEqual(newAdmin);
    });

    it('should return error if email already exists', async () => {
        Admin.findOne.mockResolvedValue({ email_address: mockAdminData.email_address });

        const result = await registerService(mockAdminData);

        expect(Admin.findOne).toHaveBeenCalledWith({ email_address: mockAdminData.email_address });
        expect(result.statusCode).toBe(400);
        expect(result.message).toBe('email address already exist');
    });

    it('should return error on internal server error', async () => {
        Admin.findOne.mockRejectedValue(new Error('Database error'));

        const result = await registerService(mockAdminData);

        expect(result.statusCode).toBe(500);
        expect(result.message).toBe('Internal Server Error');
    });
});