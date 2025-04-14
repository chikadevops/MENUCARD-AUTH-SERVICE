const { login } = require('../../controllers/auth.controller');
const { loginService } = require('../../services/auth.service');
const {
  sendErrorResponse,
  sendSuccessResponse,
} = require('../../utils/responseHandler');

jest.mock('../../utils/logger');
jest.mock('../../services/auth.service');
jest.mock('../../utils/responseHandler');

describe('Login Controller', () => {
  let req, res;

  beforeEach(() => {
    req = {
      body: { email_address: 'admin@example.com', password: 'password123' },
    };
    res = { status: jest.fn().mockReturnThis(), json: jest.fn() };
  });

  test('should return 400 if email or password is missing', async () => {
    req.body = {}; // Empty body

    await login(req, res);

    expect(sendErrorResponse).toHaveBeenCalledWith(
      res,
      400,
      'Fields are required'
    );
  });

  test('should return error if login service fails', async () => {
    loginService.mockResolvedValue({
      success: false,
      statusCode: 401,
      message: 'Invalid credentials',
    });

    await login(req, res);

    expect(sendErrorResponse).toHaveBeenCalledWith(
      res,
      401,
      'Invalid credentials'
    );
  });

  test('should return success if login is successful', async () => {
    loginService.mockResolvedValue({
      success: true,
      statusCode: 200,
      message: 'Login successful',
      data: { token: 'mocked_token' },
    });

    await login(req, res);

    expect(sendSuccessResponse).toHaveBeenCalledWith(
      res,
      200,
      'Login successful',
      { token: 'mocked_token' }
    );
  });

  test('should return 500 if an unexpected error occurs', async () => {
    loginService.mockRejectedValue(new Error('Database error'));

    await login(req, res);

    expect(sendErrorResponse).toHaveBeenCalledWith(
      res,
      500,
      'Something went wrong'
    );
  });
});
