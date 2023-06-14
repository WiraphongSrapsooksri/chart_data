
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

app.post('/Filter', (req, res) => {
   const searchData = req.body;

   const searchResults = dataALL.filter(item => {
      return searchData.type === item.type &&
         (searchData.code.includes(item.code) || searchData.code.length == 0) &&
         (searchData.date.includes(item.time.substring(0, 2)) || searchData.date.length == 0) &&
         (
            item.time.split(' & ').filter((fitem) => fitem.substring(2, 4) === searchData.time).length > 0 || searchData.time === "total"
         )
   });

   res.send(searchResults);
});


app.listen(port, () => {
   console.log("Starting node.js at port " + port);
});
