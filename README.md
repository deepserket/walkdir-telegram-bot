# Telegram Walkdir Bot

With this bot you can access your pc via telegram, navigate through directories and download the files you want

## Warnings
This bot only works on linux (maybe even on MacOS, but I have not tried it), in the future I will add support to other operating systems (Sorry, but on every feature I add support to not linux OS seems farther away ).

This script is in alpha, so there may be several problems like files that are not read etc ... (no, your pc is not likely to explode)

The telegram limit of the data that each button can hold is 64 bytes, so files or directories with a name longer than 63 bytes are not shown.

The limit of files that bots can upload is 50MB.

The code is ugly (thanks to the Terminal feature is really, really ugly).

## Configuration
Before starting up the bot you have to take care of some settings. You need to edit one file:

### SECRETS.txt
  - First line: Your user ID. The bot will only reply to messages from this user. If you don't know your user ID, send a message to `userinfobot` and he will reply your ID. If you have more than one telegram account you can enter comma-separated IDs, as in the sample file.
  
  - Second line: The token that identifies your bot. You will get this from 'BotFather' when you create your bot. If you don't know how to register your bot, follow [these instructions](https://core.telegram.org/bots#3-how-do-i-create-a-bot)
 
  - Third line (optional): The starting directory, if this line is empty there will be the directory where it is main.py


## Installation
In order to run the bot you need to execute the script `main.py`

### Prerequisites
You have to use __Python 3__ to execute the script and you need to install the following Python modules first:
```shell
pip3 install python-telegram-bot --upgrade
```

### Starting up
To start the script, execute `python3 main.py`.

## Usage
If you configured the bot correctly and execute the script, in the logs the bot will ask to send the command `/start`.
As soon as you have sent the command will appear a set of buttons, if you click on `START TERMINAL HERE` a new terminal spawn on the desktop (this function is in alpha), and you can send commands both from telegram and the new terminal, if you click on a folder (dir :) you will enter it, if you click on a file (file :) the bot will send it.


### Available commands
- `/start` Starts navigating directories, also change the current directory to the start directory
- `/stop`  Shutdown the bot (please use this command instead of ctrl-z)

## TODO
  - improve terminal feature (there are a tons of bugs)
  - write others TODO
