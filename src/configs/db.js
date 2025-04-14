const mongoose = require("mongoose");

const { config } = require("dotenv");
config();


const MONGODB_URI = process.env.NODE_ENV === 'test'
  ? process.env.TEST_MONGODB_URI
  : process.env.LIVE_MONGODB_URI

  mongoose.set('strictQuery', false)

  console.log('connecting to DB')
  
exports.DBConnection = () =>{
    mongoose.connect(MONGODB_URI)
    .then(() => {
      console.log('connected to MongoDB Successfully.')
    })
    .catch((error) => {
      console.log('error connection to MongoDB:', error.message)
    })
}