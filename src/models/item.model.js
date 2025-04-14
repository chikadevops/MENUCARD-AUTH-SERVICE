const { Schema, model } = require('mongoose');

const itemSchema = new Schema({
      item_name: {
            type: String,
            required: true
            },
      description: {
            type: String
            },
      image_url: {
            type: String
            },
      price: {
            type: Number
            },
      admin_id: {
            type: Schema.Types.ObjectId,
            ref: 'Admin',
            required: true
            },
      created_at: {
            type: Date,
            default: Date.now()
            },
      updated_at: {
            type: Date,
            default: Date.now()
            },
      is_deleted: {
            type: Boolean,
            default: false
            }
            })

itemSchema.set('toJSON', {
     transform:(document,returnedObject) => {
             returnedObject.id = returnedObject._id.toString()
             delete returnedObject._id
             delete returnedObject.__v
     }
 })

 const Item = model('Item', itemSchema)

 module.exports = Item