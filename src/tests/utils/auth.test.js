const {
  hashPassword,
  verifyPassword,
  generateToken,
  verifyAccessToken,
} = require('../../utils/auth.utils');
const logger = require('../../utils/logger');

jest.mock('../../utils/logger')

describe('Auth Utils Test: hashPassword and verifyPassword', () => {
  const password = 'password12345';
  let passwordHash;

  beforeAll(async () => {
    passwordHash = await hashPassword(password);
  });

  test('hashPassword should return a hashed password', async () => {
    expect(passwordHash).not.toBe(password);
    expect(passwordHash).toMatch(/^\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53}$/);
  });

  test('verifyPassword should correctly compare a password and hash', async () => {
    const isPasswordMatched = await verifyPassword(password, passwordHash);
    const isPasswordMatched2 = await verifyPassword(password, password);

    expect(isPasswordMatched).toBe(true);
    expect(isPasswordMatched2).toBe(false);
  });
});

describe('Auth Utils Test: generateToken and verifyAccessToken', () => {
  let token;
  const adminId = 'admin123';

  beforeAll(() => {
    process.env.JWT_TOKEN_SECRET = 'testSecretKey';
    process.env.JWT_TOKEN_LIFETIME = '30m';
    token = generateToken(adminId);
  });

  test('generateToken should return a JWT token', async () => {
    expect(token).toBeTruthy();
    expect(token).toMatch(
      /^[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+$/
    );
  });

  test('verifyAccessToken should return a JWT token', async () => {
    const decoded = verifyAccessToken(token);

    expect(decoded).toBeTruthy();
    expect(decoded.adminId).toBe(adminId);
  });

  test('should return false for an invalid token', () => {
    const invalidToken = 'invalid.token.value';

    const result = verifyAccessToken(invalidToken);

    expect(result).toBe(false);
    expect(logger.error).toHaveBeenCalledWith(
      expect.stringContaining('Invalid Access token')
    );
  });
});
