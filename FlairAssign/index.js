const snoowrap = require("snoowrap"),
    config = require("../config"),
    fs = require("fs"),
    rollcalls = JSON.parse(fs.readFileSync("./FlairAssign/rollcalls.json", "utf-8"))


const client = new snoowrap({
    userAgent: "AutieRobot",
    clientId: config.clientID,
    clientSecret: config.clientSecret,
    username: config.username,
    password: config.password
})

console.log(rollcalls)