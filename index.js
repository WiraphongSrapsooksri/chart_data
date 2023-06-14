// const express = require("express");
// const app = express();
// const port = process.env.PORT || 3000;
// const datamajor = require('./dataMajor.json')
// const datas = require("./data2.json")


// app.get("/", (req, res) => {
//    res.send("Hello! Node.js");
// });

// app.get('/datamajor', (req, res) => {
//    res.json(datas)
// })
// app.get('/Group/:id', function (req, res) {
//    res.send(req.params.id);
// });

// app.listen(port, () => {
//    console.log("Starting node.js at port " + port);
// });
const express = require("express");
const app = express();
const port = process.env.PORT || 3000;
const datas = require("./data2.json");

app.get("/", (req, res) => {
   res.send("DATA REG");
});

app.get('/datamajor', (req, res) => {
   res.json(datas);
});

app.get('/Group/:id', (req, res) => {
   const groupId = req.params.id;
   const groupData = datas.filter(data => data.group === groupId);

   if (groupData.length > 0) {
      res.json(groupData);
   } else {
      res.status(404).send("Group not found");
   }
});

app.listen(port, () => {
   console.log("Starting node.js at port " + port);
});
