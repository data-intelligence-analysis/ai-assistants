require("dotenv").config({ path: __dirname + "/.env" });

const { TwitterApi } = require("twitter-api-v2");
const CronJob = require("cron").CronJob;
//file
const fs = require("fs");
const express = require('express')
const app = express()
const port = process.env.PORT || 4000;
const { download } = require("./utilities");

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

//Helpers
/*const tweet = async () => {
  try {
    console.log('Loading Tweet....')
    await twitterClient.v2.tweet("Test");
    console.log('Successfully delivered Tweet')
  } catch (e) {
    console.log(e)
  }
}*/
//Obtain image from external URI
/*const tweetImgExternal = async () => {
  const uri = "https://i.imgur.com/Zl2GLjnh.jpg";
  const filename = "image.png";
  download(uri, filename, async function(){
      try {
          const mediaId = await twitterClient.v1.uploadMedia("./image.png");
          await twitterClient.v2.tweet({
              text: "Hello world! This is an image in Ukraine!",
              media: {
                  media_ids: [mediaId]
              }
          });
      } catch (e) {
          console.log(e)
      }
  });
}*/

//Main
/*const texts = [
  "Msjorji is back 🔥 #thankful #Herewego #ATX #Austinmusic #undergroundhiphop #Texasmusic #mixtapealert",
  "Who is this? #Herewego #ATX #Austinmusic #undergroundhiphop #Texasmusic #mixtapealert",
  "Austin music is taking over #Herewego #ATX #Austinmusic #undergroundhiphop #Texasmusic #mixtapealert",
  "Check out new music from Msjorji #Herewego #ATX #Austinmusic #undergroundhiphop #Texasmusic #mixtapealert",
  "Msjorji Killing the game right now #Herewego #ATX #Austinmusic #undergroundhiphop #Texasmusic #mixtapealert",
]*/
const texts = [
  "Test1",
  "Test2",
  "Test3",
  "Test4",
  "Test5"
]
const randomSelection = () => {
  let usedMessages = []
  // base case
  if (texts.length === 0){
    console.log("All messages have been used.")
    return null;
  }
  const randomIndex = Math.floor(Math.random() * texts.length)
  const randomMessage = texts[randomIndex]
  texts.splice(randomIndex, 1);
  usedMessages.push(randomMessage);
  return randomMessage;
}

//listen on a specfic port when server begins
app.listen(port, () => {
  console.log(`Listening on port ${port}`)
})

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
function setDaysTimeout(callback,days) {
  // 86400 seconds in a day - used to run the timer every day and check for days set to run the timeout
  let msInDay = 86400*1000; 

  let dayCount = 0;
  let timer = setInterval(() => {
      dayCount++;  // a day has passed
      if (dayCount === days) {
         clearInterval(timer);
         callback.apply(this, []);
      }
  }, msInDay);
}

//Time Utility
// Set the stop day and time in HH:mm format (24-hour clock)
const startTime = "20:21" //in HH:mm format (24-hour clock)
const startDay = '3'; // Sunday is 0, Monday is 1, and so on
const [startHour, startMinute] = startTime.split(':');
// Set the stop time in HH:mm format (24-hour clock)
const stopTime = '21:00';
const stopYear = '2023';
const stopMonth = '11'; // January is 0, December is 11, and so on
const stopDay = '23';
const stopMilliseconds = '0'
const [stopHour, stopMinute] = stopTime.split(':');
const now = new Date();
//const stopDate = new Date(now.getFullYear(), now.getMonth(), now.getDate(), stopHour, stopMinute);
const stopDate = new Date(stopYear, stopMonth, stopDay, stopHour, stopMinute, stopMilliseconds);
const timeUntilStop = stopDate.getTime() - now.getTime();

const minute = 1000 * 60
const hour = minute * 60
const day = hour * 24;
const daysUntilStop = Math.floor(timeUntilStop / day) === 0 ? (Math.floor(timeUntilStop / day)) + 1 : Math.floor(timeUntilStop / day);
//console.log(now);
//console.log(stopDate);
//console.log(daysUntilStop);
// Schedule the cron job to run every week at the specified day and time
const cronTweet = new CronJob(`0 ${startMinute} ${startHour} * * ${startDay}`, 
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
/*setTimeout(() => {
  console.log('Stopping cron job...');
  cronTweet.stop();
  console.log('Cron job has stopped');
}, timeUntilStop);*/
