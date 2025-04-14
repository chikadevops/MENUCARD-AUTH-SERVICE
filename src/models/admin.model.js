const { Schema, model } = require('mongoose');

const adminSchema = new Schema({
  full_name: {
    type: String,
    required: true,
  },
  restaurant_name: {
    type: String,
    required: false,
    unique: true,
  },
  email_address: {
    type: String,
    required: true,
    unique: true,
    match: [
      /^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/,
      'Please add a valid email',
    ],
  },
  phone_number: {
    type: String,
    required: true,
    unique: true,
  },
  passwordHash: {
    type: String,
    required: true,
  },
  image_url: {
    type: String,
  },
  created_at: {
    type: Date,
    default: Date.now(),
  },
});

adminSchema.set('toJSON', {
  transform: (document, returnedObject) => {
    returnedObject.id = returnedObject._id.toString();
    delete returnedObject._id;
    delete returnedObject.__v;
    delete returnedObject.passwordHash;
  },
});

const Admin = model('Admin', adminSchema);

module.exports = Admin;
