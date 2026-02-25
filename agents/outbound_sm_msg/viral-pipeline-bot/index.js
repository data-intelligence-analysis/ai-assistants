require("dotenv").config({ path: __dirname + "/.env" });
const cron = require('node-cron');
const { TwitterApi } = require("twitter-api-v2");
const CronJob = require("cron").CronJob;
//file
const fs = require("fs");
//const express = require('express')
//const app = express()
const port = process.env.PORT || 4000;
//const replitUrl = 'https://replit.com/@data-intelligen/4242525tw1tt3r-wuqygtb5r-int3grt10npp5'; // Replace 'your-replit-project-url' with your Replit project URL
const replitUrl = 'https://4242525tw1tt3r-wuqygtb5r-int3grt10npp5.data-intelligen.repl.co';
const server_alive = require("./server_alive.js")

//client keys
const client = new TwitterApi({
  appKey: process.env.API_KEY,
  appSecret: process.env.API_SECRET,
  accessToken: process.env.ACCESS_TOKEN,
  accessSecret: process.env.ACCESS_SECRET,
});
const bearer = new TwitterApi(process.env.BEARER_TOKEN);

//to send tweets (write)
const twitterClient = client.readWrite;
//to read tweets (read)
const twitterBearer = bearer.readOnly;

/**********Main***********/
const texts = [
  `Msjorji is back 🔥
  
  Music Video: https://youtu.be/q5JfYup-v1c?si=e3uX8XqS9H8u1oR-
  
  Music Links: https://linktr.ee/Ms.JORJI
  
  #thankful #Herewego #ATX #Austinmusic #undergroundhiphop #Texasmusic #mixtapealert
  `,
  `Who is this? 
  
  Music Video: https://youtu.be/q5JfYup-v1c?si=e3uX8XqS9H8u1oR-
  
  #thankful #Herewego #ATX #Austinmusic #undergroundhiphop #Texasmusic #mixtapealert
  `,
  `Austin music is taking over
  
  Music Video: https://youtu.be/q5JfYup-v1c?si=e3uX8XqS9H8u1oR-
  
  Music Links: https://linktr.ee/Ms.JORJI
  
  #thankful #Herewego #ATX #Austinmusic #undergroundhiphop #Texasmusic #mixtapealert
  `,
  `Check out new music from Msjorji
  
  Music Video: https://youtu.be/q5JfYup-v1c?si=e3uX8XqS9H8u1oR-
  
  #thankful #Herewego #ATX #Austinmusic #undergroundhiphop #Texasmusic #mixtapealert
  `,
  `Msjorji Killing the game right now
  
  Music Video: https://youtu.be/q5JfYup-v1c?si=e3uX8XqS9H8u1oR-
  
  Music Links: https://linktr.ee/Ms.JORJI
  
  #thankful #Herewego #ATX #Austinmusic #undergroundhiphop #Texasmusic #mixtapealert
  `,
]
const randomSelection = () => {
  let usedMessages = []
  // base case
  if (texts.length === 0) {
    console.log("All messages have been used.")
    return null;
  }
  const randomIndex = Math.floor(Math.random() * texts.length)
  const randomMessage = texts[randomIndex]
  texts.splice(randomIndex, 1);
  usedMessages.push(randomMessage);
  return randomMessage;
}

// Middleware to log each request
/*app.use((req, res, next) => {
  console.log(`Received request at ${new Date().toLocaleString()}`);
  next();
});
//listen on a specfic port when server begins
app.listen(port, () => {
  console.log(`Listening on port ${port}`)
})
// Route to keep the project awake
app.get('/', (req, res) => {
  res.send('Bot is alive!');
});*/

const keepAlive = () => {
  // Perform a simple GET request to keep the project awake
  fetch(replitUrl)
    .then(() => console.log('Ping sent to keep the bot alive.'))
    .catch(err => console.error('Error while sending ping:', err));
}
// Make an initial call to keep the project awake
keepAlive();
// Schedule periodic calls (e.g., every 5 minutes)
setInterval(keepAlive, 300000); // 300,000 milliseconds = 5 minutes

// Schedule the cron job to run every hour
cron.schedule('0 * * * *', () => {
  // Call the necessary functions to keep the bot alive here
  console.log('Running cron job to keep the bot alive...');
});

const tweetWithImage = async () => {
  const mediaPath = './image.png';
  try {
    const mediaId = await twitterClient.v1.uploadMedia(mediaPath);
    console.log('Loading Tweet....')
    const tweet = randomSelection()
    await twitterClient.v2.tweet({
      text: `${tweet}`,
      media: {
        media_ids: [mediaId]
      }
    });
    console.log('Successfully delivered Tweet')
  } catch (e) {
    console.log(e)
  }
}
function setDaysTimeout(callback, days) {
  // 86400 seconds in a day - used to run the timer every day and check for days set to run the timeout
  let msInDay = 86400 * 1000;
  let dayCount = 0;
  let timer = setInterval(() => {
    dayCount++;  // a day has passed
    if (dayCount === days) {
      clearInterval(timer);
      callback.apply(this, []);
    }
  }, msInDay);
}

/***Time Utility***/
// Set the stop day and time in HH:mm format (24-hour clock)
const startTime = "14:30" //in HH:mm format (24-hour clock)
const startDay = '4'; // Sunday is 0, Monday is 1, and so on
const [startHour, startMinute] = startTime.split(':');


const stopTime = '10:30'; // Set the stop time in HH:mm format (24-hour clock)
const stopYear = '2023';
const stopMonth = '10'; // January is 0, December is 11, and so on
const stopDay = '8';
const stopMilliseconds = '0'
const [stopHour, stopMinute] = stopTime.split(':');
const now = new Date();
const stopDate = new Date(stopYear, stopMonth, stopDay, stopHour, stopMinute, stopMilliseconds);
const timeUntilStop = stopDate.getTime() - now.getTime();

// Check if the stop time has passed
const minute = 1000 * 60
const hour = minute * 60
const day = hour * 24;
const daysUntilStop = Math.floor(timeUntilStop / day)

// Schedule the cron job to run every week at the specified day and time
const cronTweet = new CronJob(`0 ${startMinute} ${startHour} * * *`,
  async () => {
    console.log(`Cron Job is running. [${now}]`)
    tweetWithImage();
  },
  null,
  false,
  "America/Chicago",
);
cronTweet.start();
//stop the job when timer reaches
setDaysTimeout(() => {
  console.log('Stopping cron job...');
  cronTweet.stop();
  console.log('Cron job has stopped');
}, daysUntilStop);


