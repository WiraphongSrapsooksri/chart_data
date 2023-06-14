
const express = require("express");
const app = express();
const port = process.env.PORT || 3000;
const dataALL = require("./Group/dataALL.json")
var cors = require('cors')
app.use(express.json());
app.use(cors())


app.get("/", (req, res) => {
   res.send("DATA REG");
});

app.get('/datamajor', (req, res) => {
   res.json(dataALL);
});

app.get('/Group/:id', (req, res) => {
   const groupId = req.params.id;
   try {
      const data = require("./Group/G" + groupId + ".json")

      if (data.length > 0) {
         res.json(data);
      } else {
         res.status(404).send("Group not found");
      }
   } catch {
      res.status(404).send("Group not found");
   }
});

app.get('Filter/day/:id', (req, res) => {
   const id = req.params.id;
   try {
      const data = require("./Group/dataALL.json")
      if (data.length > 0) {
         res.json(data);
      } else {
         res.status(404).send("Group not found");
      }
   } catch {
      res.status(404).send("Group not found");
   }
})
// "time": "Fr08:00-10:00 IT-507 & We13:00-15:00 IT-507"

app.post('/Filter', (req, res) => {
   const searchData = req.body;
   // console.log(searchData.code);
   const data = require("./Group/dataALL.json")
   const searchResults = data.filter(item => {
      return searchData.type === item.type &&
         searchData.code.includes(item.code) &&
         searchData.date.includes(item.time.substring(0, 2)) &&
         (
            item.time.split(' & ').filter((fitem) => fitem.substring(2, 4) === searchData.time).length > 0 || searchData.time === "total"
         )
   });
   // console.log(searchResults);
   res.send(searchResults);
});


app.listen(port, () => {
   console.log("Starting node.js at port " + port);
});
