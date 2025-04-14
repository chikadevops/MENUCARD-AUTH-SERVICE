const { config } = require("dotenv")
const { DBConnection } = require("./src/configs/db.js")
const { app } = require("./src/app.js")

config()
DBConnection()

const PORT = process.env.PORT || 8080

app.listen(PORT, () =>{
   console.log(`App is running on port ${PORT}`)
})

