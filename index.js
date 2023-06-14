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

// app.get('/datamajor/:code', (req, res) => {
//    res.json(datamajor.find(data =>
//       console.log(data)
//       // data => data.code === Number(req.params.code)
//       ))
// })

app.listen(port, () => {
   console.log("Starting node.js at port " + port);
});