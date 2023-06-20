
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

app.get('/seccount/:type', (req, res) => {
   const type = req.params.type;
   try {
      const filteredData = dataALL.filter(item => item.type === type);
      const result = filteredData.map(item => ({
         code: item.code,
         name: item.name
      }));

      const mergedObjects = [];

      result.map(data => {
         if (!mergedObjects.map(mo => mo.code).includes(data.code)) {
            mergedObjects.push({
               ...data,
               sec_count: filteredData.filter(df => df.code === data.code).length
            })
         }
      })

      res.json(mergedObjects);
   } catch (error) {
      res.status(404).send("Not found");
   }
});

app.post('/Filter', (req, res) => {
   try {
      const searchData = req.body;
      const searchResults = dataALL.filter(item => {
         return searchData.type === item.type ||
            (searchData.code.includes(item.code) || searchData.code.length == 0) &&
            (searchData.date.includes(item.time.substring(0, 2)) || searchData.date.length == 0) &&
            (
               item.time.split(' & ').filter((fitem) => fitem.substring(2, 4) === searchData.time).length > 0 || searchData.time === "total"
            )
      });
      res.send(searchResults);
   } catch {
      res.status(404).send("Not found");
   }
});

app.listen(port, () => {
   console.log("Starting node.js at port " + port);
});

// Run a schedule
console.log("Running schedule...");
// Add your code here to run the schedule
const cron = require('node-cron');
const { exec } = require('child_process');
const path = require('path');

// Run the Python file every 10 seconds
sec = 30
cron.schedule(`*/${sec} * * * * *`, () => {
   exec(`cd ${path.dirname(__filename)} && python ./main.py`, (error, stdout, stderr) => {
      if (error) {
         console.error(`exec error: ${error}`);
         return;
      }
      // saving timestamp to log file
      const fs = require('fs');
      const stamp = new Date().toISOString() + "\n";
      fs.appendFile('log.txt', stamp, function (err) {
         if (err) throw err;
      }
      );
   });
});
