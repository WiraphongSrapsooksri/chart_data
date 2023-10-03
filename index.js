
const express = require("express");
const app = express();
const fs = require('fs');
const port = process.env.PORT || 3030;
// Check has file
// Add your code here to run the schedule
const cron = require('node-cron');
const path = require('path');
const { exec } = require('child_process');
const dataALLPath = "./Group/MSU/dataALL.json";
if (!fs.existsSync(dataALLPath)) {
   console.error(`File ${dataALLPath} does not exist`);
   exec(`cd ${path.dirname(__filename)} && python ./main.py`, (error, stdout, stderr) => {
      if (error) {
         console.error(`exec error: ${error}`);
         return;
      }
   });
}

var dataALL = require(dataALLPath);

var cors = require('cors')
app.use(express.json());
app.use(cors())

var cache_updated = "none"

var ready = false;

app.get("/", (req, res) => {
   res.send("DATA REG");
});

app.get('/datamajor', (req, res) => {
   res.json(dataALL);
});

app.get('/Group/:id', (req, res) => {
   const groupId = req.params.id;
   const universal = "MSU";
   try {
      const data = require("./Group/" + universal + "/G" + groupId + ".json")

      if (data.length > 0) {
         res.json(data);
      } else {
         res.status(404).send("Group not found");
      }
   } catch {
      res.status(404).send("Group not found");
   }
});

app.post('/seccount/:type', (req, res) => {
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

app.post('/updated', (req, res) => {
   res.send(JSON.stringify(cache_updated));
});

app.post('/Filter', (req, res) => {
   try {
      const searchData = req.body;
      const universal = "MSU";
      fs.readFile('Group/' + universal + '/dataALL.json', 'utf8', (err, data) => {
         if (err) {
            console.error(err);
            return res.status(404).send("Not found");
         }
         const dataALL = JSON.parse(data);
         const searchResults = dataALL.filter(item => {
            return (searchData.type.includes(item.type) || searchData.type.length == 0) &&
               (searchData.code.includes(item.code) || searchData.code.length == 0) &&
               (searchData.date.includes(item.time.substring(0, 2)) || searchData.date.length == 0) &&
               (
                  item.time.split(' & ').filter((fitem) => fitem.substring(2, 4) === searchData.time).length > 0 || searchData.time === "total"
               )
         });

         // Sort the search results by remaining most
         searchResults.sort((a, b) => {
            return b.remaining - a.remaining;
         });

         res.send(searchResults);
      });
   } catch {
      res.status(404).send("Not found");
   }
});

app.listen(port, () => {
   console.log("Starting node.js at port " + port);
   ready = true;
});

// Run a schedule
console.log("Running schedule...");

// Run the Python file
const args = require('minimist')(process.argv.slice(2));
const sec = args.t || 10;

var seconds = sec;
var count = 0;

const scheduledFunction = () => {
   if (!ready) return;

   if (cache_updated === "none" && seconds === sec) {
      seconds = 0;
   }

   if (seconds > 0) {
      process.stdout.write(`\x1b[K\x1b[90mRequested done on\x1b[0m ${cache_updated} \x1b[90m(${count}) \x1b[33m| \x1b[37m${seconds}\x1b[33m's left...\r`);
      seconds--;
      return
   } else if (seconds == 0) {
      seconds = -1;

      if (cache_updated === "none") {
         process.stdout.write(`\x1b[K\x1b[90mFirst Running \x1b[33m| \x1b[32mUpdating...\r`);
      } else {
         process.stdout.write(`\x1b[K\x1b[90mRequested done on\x1b[0m ${cache_updated} \x1b[33m| \x1b[90m${count} \x1b[33m| \x1b[32mUpdating...\r`);
      }

      exec(`cd ${path.dirname(__filename)} && python ./main.py`, (error, stdout, stderr) => {
         if (error) {
            console.error(`exec error: ${error}`);
            return;
         }
         cache_updated = new Date().toLocaleDateString('th-TH', {
            year: '2-digit',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
         }).replace(',', '');

         seconds = sec;
         count++;
      });
   }
}

cron.schedule('* * * * * *', scheduledFunction);