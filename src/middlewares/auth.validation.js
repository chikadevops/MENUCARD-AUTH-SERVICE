const Joi = require('joi');
const { sendErrorResponse } = require('../utils/responseHandler');

const fieldSchemas = {
  full_name: Joi.string().min(3).max(50).messages({
    'string.empty': 'Full name is required',
    'string.min': 'Full name must be at least 3 characters long',
    'string.max': 'Full name must not exceed 50 characters',
  }),

  email_address: Joi.string().email().lowercase().trim().messages({
    'string.empty': 'Email address is required',
    'string.email': 'Invalid email format',
  }),

  phone_number: Joi.string()
    .pattern(/^\+?[0-9]{7,15}$/)
    .messages({
      'string.empty': 'Phone number is required',
      'string.pattern.base': 'Invalid phone number format',
    }),

  password: Joi.string()
    .min(8)
    .max(20)
    .pattern(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%#./*?&])[A-Za-z\d@$!%#./*?&]{8,}$/)
    .messages({
      'string.empty': 'Password is required',
      'string.min': 'Password must be at least 8 characters long',
      'string.max': 'Password must not exceed 20 characters',
      'string.pattern.base': 'Password must contain at least one uppercase letter, one lowercase letter, one number and one special character',
    }),

  restaurant_name: Joi.string().min(3).max(100).messages({
    'string.empty': 'Restaurant name is required',
    'string.min': 'Restaurant name must be at least 3 characters long',
    'string.max': 'Restaurant name must not exceed 100 characters',
  }),
};



const schemas = {
  // Define complete schemas for different POST requests
  register: Joi.object({
    full_name: fieldSchemas.full_name.required(),
    email_address: fieldSchemas.email_address.required(),
    phone_number: fieldSchemas.phone_number.required(),
    password: fieldSchemas.password.required(),
    confirm_password: Joi.string().valid(Joi.ref('password')).required()
      .messages({
        'any.only': 'Passwords must match',
        'string.empty': 'Password confirmation is required'
      }),
    restaurant_name: fieldSchemas.restaurant_name
  }),


  login: Joi.object({
    email_address: fieldSchemas.email_address.required(),
    password: fieldSchemas.password.required()
  }),
};

// Validation middleware
const validate = (schema) => {
  return (req, res, next) => {
    const { error, value } = schema.validate(req.body, {
      abortEarly: false,
    });

    if (error) {
      return sendErrorResponse(res, 400, error.details.map(err => err.message).join(', '));
    }

    req.body = value;
    next();
  };
};

module.exports = {
  schemas,
  validate,
};
