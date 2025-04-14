const Admin = require('../../models/admin.model');
const { loginService } = require('../../services/auth.service');
const {
  errorResponse,
  successResponse,
} = require('../../utils/responseHandler');
const { verifyPassword, generateToken } = require('../../utils/auth.utils');

jest.mock('../../utils/logger');
jest.mock('../../utils/auth.utils');
jest.mock('../../models/admin.model');
jest.mock('../../utils/responseHandler');

describe('Auth Service - Login', () => {
  const mockExistingAdmin = {
    full_name: 'Test Admin',
    email_address: 'test@test.com',
    phone_number: '1234567890',
    passwordHash: 'hashedPassword123',
    restaurant_name: 'Test Restaurant',
    _id: 'someId123',
  };

  const errorResponseObject = {
    statusCode: 400,
    message: 'Invalid email address or password',
  };

  const handleDBOrUnexpectErrorTest = async () => {
    errorResponse.mockReturnValue({
      statusCode: 500,
      message: 'Something Went Wrong',
    });

    const result = await loginService({
      email_address: mockExistingAdmin.email_address,
      password: 'testpass123',
    });

    expect(errorResponse).toHaveBeenCalledWith(500, 'Something Went Wrong');
    expect(result).toEqual({
      statusCode: 500,
      message: 'Something Went Wrong',
    });
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should return success response if admin exists and passwor is correct', async () => {
    const token = 'mockToken123';
    const password = 'testpass123';

    Admin.findOne.mockResolvedValue(mockExistingAdmin);
    verifyPassword.mockResolvedValue(true);
    generateToken.mockReturnValue(token);

    successResponse.mockReturnValue({
      statusCode: 200,
      message: 'Admin Login Successfully',
      data: { admin: mockExistingAdmin, token },
    });

    const result = await loginService({
      email_address: mockExistingAdmin.email_address,
      password,
    });

    expect(Admin.findOne).toHaveBeenCalledWith({
      email_address: mockExistingAdmin.email_address,
    });

    expect(verifyPassword).toHaveBeenCalledWith(
      password,
      mockExistingAdmin.passwordHash
    );

    expect(generateToken).toHaveBeenCalledWith(mockExistingAdmin._id);
    expect(successResponse).toHaveBeenCalledWith(
      200,
      'Admin Login Successfully',
      { admin: mockExistingAdmin, token: 'mockToken123' }
    );

    expect(result).toEqual({
      statusCode: 200,
      message: 'Admin Login Successfully',
      data: { admin: mockExistingAdmin, token: 'mockToken123' },
    });
  });

  it('should return error if admin does not exist', async () => {
    Admin.findOne.mockResolvedValue(null);
    errorResponse.mockReturnValue(errorResponseObject);

    const result = await loginService({
      email_address: 'nonexistent@test.com',
      password: 'wrongpass',
    });

    expect(Admin.findOne).toHaveBeenCalledWith({
      email_address: 'nonexistent@test.com',
    });

    expect(errorResponse).toHaveBeenCalledWith(
      400,
      'Invalid email address or password'
    );

    expect(result).toEqual(errorResponseObject);
  });

  it('should return error if password is incorrect', async () => {
    Admin.findOne.mockResolvedValue(mockExistingAdmin);
    verifyPassword.mockResolvedValue(false);

    errorResponse.mockReturnValue(errorResponseObject);

    const result = await loginService({
      email_address: mockExistingAdmin.email_address,
      password: 'wrongpass',
    });

    expect(Admin.findOne).toHaveBeenCalledWith({
      email_address: mockExistingAdmin.email_address,
    });

    expect(verifyPassword).toHaveBeenCalledWith(
      'wrongpass',
      mockExistingAdmin.passwordHash
    );
    expect(errorResponse).toHaveBeenCalledWith(
      400,
      'Invalid email address or password'
    );
    expect(result).toEqual(errorResponseObject);
  });

  it('should return 500 if database error occurs', async () => {
    Admin.findOne.mockRejectedValue(new Error('Database error'));
    handleDBOrUnexpectErrorTest();
  });

  it('should return 500 on an unexpected error', async () => {
    Admin.findOne.mockResolvedValue(mockExistingAdmin);
    verifyPassword.mockImplementation(() => {
      throw new Error('Unexpected error');
    });
    handleDBOrUnexpectErrorTest();
  });
});
