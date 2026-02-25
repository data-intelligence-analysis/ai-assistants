//For Running apps on online integrated development environment
require("dotenv").config({ path: __dirname + "/.env" });
var http = require('http');
const port = 8080;

http.createServer(function (req, res) {
    res.write('Server is alive');
    res.end();
}).listen(port); //listen on port 8080