# Discord2VRC

A simple Discord bot and a web server that allows you to load images that have been uploaded to select discord channels into VRChat worlds directly. 
As this was primarily a project I started for personal use, the way it has been set up is mainly catered to what was convenient for me, which may not neccessarily be the case for others. I may not have used the best practices for the sake of convenience, so keep that in mind if you are interested in using this. This is only for SDK2 worlds for now until Udon receives support for loading remote images. 

![demo](https://nyanpa.su/i/rC6o1rMW.gif)

# Web server 

API Documentation: https://discord2vrc.nyanpa.su/docs
Feel free to play around with the sample web app I have set up above to see how the web end points work. 
There are 2 channel "aliases" set up "vrchat" and "ffxiv".

Of note, the randomsync endpoints will return a random image using the current server time based on intervals.
That means reloading the image in vrchat should show the same random image to everyone in the instance as long as they load it at the same time for the most part.

# Discord bot

Commands are as follows
```md
Admin:
  clear       clear channel of bot messages,
  extensions  Shows extensions available and loaded
  load        Load extension, eg. !load image
  ping        Ping!
  quit        Tells bot to quit
  reload      Reload extension, eg. !reload image
  unload      Unload extension, eg. !unload image
Image:
  alias       Sets an alias for current channel's subscription
  purge       Soft deletes all images downloaded from this channel
  reactclear  Clear bot reactions from this channel,
  rescan      Rescans current channel for images if it is subscribed
  status      Shows current channels subscription status
  subscribe   Subscribe current channel for image crawling
  unsubscribe Unsubscribe current channel for image crawling
​No Category:
  help        Shows this message

Type !help command for more info on a command.
You can also type `help category for more info on a category.
```
Use help on specific commands for more information

# Requirements

MongoDB
Python 3.7+
  - [Discord.py](https://github.com/Rapptz/discord.py)
  - [FastAPI](https://github.com/tiangolo/fastapi)
  - [AIOFiles](https://github.com/Tinche/aiofiles)
  - [Odmantic](https://github.com/art049/odmantic)
  - [Uvicorn](https://github.com/encode/uvicorn)


# Installation

Make sure python 3.7+ and MongoDB are installed first

```bash
git clone https://github.com/acertainbluecat/Discord2VRC.git
cd Discord2VRC
python3 -m pip install -r requirements.txt
cd app
```
Fill up config.ini with the relevant information before running 
```bash
python3 migrate.py
```
Start the bot and web server
```bash
python3 bot.py
uvicorn web:app --port 80
```
Ideally, consider running behind nginx with gunicorn to manage uvicorn workers


# SDK2

The provided unitypackage for sdk2 uses vrc_panorama to load remote images. In it are 2 sample prefabs that are currently set to load sample endpoints I have set up for demonstration purposes that loads the latest image and a randomly selected pseudo sync'd image that can be dynamically reloaded at runtime. Replace the URLs with your own. 

# Todo

  - Image collage
  - Videos