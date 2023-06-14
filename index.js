const express = require("express");
const app = express();
const port = process.env.PORT || 3000;
const datamajor = require('./dataMajor.json')
const datas = require("./data2.json")


app.get("/", (req, res) => {
   res.send("Hello! Node.js");
});

app.get('/datamajor', (req, res) => {
   res.json(datas)
})
app.get('/Group/:id', function (req, res) {
   res.send('Group' + req.params.id);
});

app.listen(port, () => {
   console.log("Starting node.js at port " + port);
});