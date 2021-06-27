# Discord2VRC

A simple Discord bot and a web server that allows you to load images that have been uploaded to select discord channels into VRChat worlds directly. 

As this was primarily a project I started for personal use, the way it has been set up is mainly catered to what was convenient for me, which may not neccessarily be the case for others. I may not have used the best practices for the sake of convenience, so keep that in mind if you are interested in using this. 

If you're looking for a simple drag and drop prefab please be aware that this is not one of them and requires some technical knowledge as well as your own server to set this up on.

This is only for SDK2 worlds for now until Udon receives support for loading remote images. Once that happens I will likely make proper Udon slideshow prefabs that make full use of the web endpoints. The provided sdk2 prefab is just a minimal example.

![demo](https://nyanpa.su/i/rC6o1rMW.gif)

# Requirements

MongoDB

Python 3.7+
  - [Discord.py](https://github.com/Rapptz/discord.py)
  - [FastAPI](https://github.com/tiangolo/fastapi)
  - [AIOFiles](https://github.com/Tinche/aiofiles)
  - [Odmantic](https://github.com/art049/odmantic)
  - [Uvicorn](https://github.com/encode/uvicorn) or an ASGI server of your choice

Discord Bot Permissions
  - Send Messages
  - Manage Messages
  - Read Message History
  - Add Reactions
  - View Channels

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
Create a placeholder.png and put it in your static dir or use the one from app/static (Used to display when VRC endpoints return a 404)

Start the bot and web server
```bash
python3 bot.py
uvicorn web:app --port 80
```
Ideally, consider running behind nginx with gunicorn to manage uvicorn workers

# How to use

The bot is currently configured to only listen to owners defined in config.ini.  
I may in future add a simple ACL to replace this behaviour instead.

Invite the bot to your discord server.  
Use the following command in the respective channel to subscribe to it.
```
!subscribe [alias]
```
Where [alias] is an optional parameter, if omitted the alias will be set to the channel name. The alias is used to load images specifically from this channel from the web url endpoints. The bot will now listen to the channel and upload image attachments posted. Images uploaded will be converted to jpg with quality at 80.

To upload images that were posted before, call the following command in the respective channel.
```
!rescan [limit]
```
Where [limit] is an optional parameter, refers to how many messages back the bot will check for images. Defaults to 100, adjust as neccessary, though higher numbers will take longer.

To clear images from a respective channel.
```
!purge
```
Will mark all images in the channel as deleted, and they will not show up in the vrc web endpoints, but will still be returned in the api. 

You can use these 2 commands to manage what images you want to be returned by the web endpoints by purging, editing/deleting images in the channel as desired and rescanning. I may in future add more granular commands for management of images.

The provided unitypackage for sdk2 uses vrc_panorama to load remote images. In it are 2 sample prefabs that are currently set to load sample endpoints I have set up for demonstration purposes that loads the latest image and a randomly selected pseudo sync'd image that can be dynamically reloaded at runtime. Replace the domain name in the urls with your own. 

For details on available web endpoints and other bot commands see below.

# Web server 

API Documentation: https://discord2vrc.nyanpa.su/docs

Feel free to play around with the sample web app I have set up above to see how the web end points work. There are 2 channel "aliases" set up "vrchat" and "ffxiv".

The VRC endpoints are to be used for vrchat and will return a single image. They can be used with vrc_panorama on sdk2 to load images dynamically as they are reloaded by respawning the vrc_panorama prefab. As the endpoints redirect instead of returning images directly, there shouldnt be an issue with caching.

Of note, the randomsync endpoints will return a random image using the current server time based on intervals. That means reloading the image in vrchat should show the same random image to everyone in the instance as long as they load it at the same time for the most part. 

This can be used to create a slideshow prefab that is sync'd for everyone, but ideally wait for Udon support for remote images due to sdk2 limitations that might make this unfeasible on sdk2.

# Discord bot

Commands are as follows
```
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
No Category:
  help        Shows this message

Type !help command for more info on a command.
You can also type `help category for more info on a category.
```
Use help on specific commands for more information

# Todo

  - Udon slideshow prefab (when it supports remote images)
  - Image collage
  - Videos