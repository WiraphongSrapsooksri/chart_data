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
    });
});