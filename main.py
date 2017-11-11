import os
import logging
import threading
from time import sleep

from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (Updater, CallbackQueryHandler, MessageHandler, Filters,
                          CommandHandler)

from term_utils import Terminal

logging.basicConfig(level=logging.DEBUG,
                  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

with open("SECRETS.txt", "r") as f:
    ADMINS = [int(n) for n in f.readline().strip().split(',')]
    BOT_TOKEN = f.readline().strip()
    
    START_DIR = f.readline().strip()
    if not START_DIR:
        START_DIR = os.getcwd()

term = Terminal(START_DIR)

last_message_id = None # TODO remove weird globals
last_chat_id = None
bot_ = None

logger.info("Starting the bot... send me a /start command!")

def start(bot, update):
    global bot_
    bot_ = bot
    logger.info("from {}: /start".format(update.message.chat_id))

    if update.message.chat_id not in ADMINS:
        update.message.reply_text("You aren't an admin!")
        
        for id_ in ADMINS: # Warning to the admins
            bot.send_message(chat_id=id_,
                   text="{} attempted to access".format(update.message.chat_id))
        return
    
    term.current_dir = term.start_dir
    reply_markup = InlineKeyboardMarkup(term.create_keyboard())
    update.message.reply_text(term.current_dir, reply_markup=reply_markup)


def refresh_stdout_on_telegram():
    old_lines = ''
    
    # TODO add command buttons
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton('stop terminal', 
                                                          callback_data=' s')]])
    while term.is_started_real_terminal:
        sleep(0.1)
        if old_lines == term.text_stdout: # no changes...
            continue
        
        old_lines = term.text_stdout
        
        bot_.edit_message_text(chat_id=last_chat_id,
                               message_id=last_message_id,
                               text=old_lines+'_',
                               reply_markup=reply_markup)


def callback(bot, update):
    global last_message_id, last_chat_id
    query = update.callback_query
    
    if query.message.chat_id not in ADMINS:
        return # without this the bot can be craked: https://github.com/python-telegram-bot/python-telegram-bot/issues/709
    
    # MODE: d -> directory, f -> file, w -> change window, t -> start real term
    #       s -> stop real term,         TODO c -> term commands (ctrl-z, ctrl-c, and so on....)
    path, mode = query.data[:-1], query.data[-1]
    
    if mode == 'd': # directory
        term.cd(path)
        reply_markup = InlineKeyboardMarkup(term.create_keyboard())
        bot.edit_message_text(chat_id=query.message.chat_id,
                    text="current directory: \n{}".format(term.current_dir),
                    message_id=query.message.message_id,
                    reply_markup=reply_markup)
        
    elif mode == 'f': # file
        bot.edit_message_text(text="sending {}...".format(path),
                                chat_id=query.message.chat_id,
                                message_id=query.message.message_id)
        
        path = os.path.join(term.current_dir, path)
        bot.send_document(chat_id=query.message.chat_id, document=open(path, 'rb'))
        
        logger.info("{} downloaded {}".format(query.message.chat_id, path))
        
        reply_markup = InlineKeyboardMarkup(term.create_keyboard())
        bot.send_message(chat_id=query.message.chat_id,
                      text='current directory: \n{}'.format(term.current_dir),
                      reply_markup=reply_markup)
    
    elif mode == 'w': # change window
        new_window = int(path)
        
        reply_markup = InlineKeyboardMarkup(term.create_keyboard(window=new_window))
        bot.edit_message_text(chat_id=query.message.chat_id,
                        text="current directory: \n{}".format(term.current_dir),
                        message_id=query.message.message_id,
                        reply_markup=reply_markup)
    
    elif mode == 't': # start real terminal
        last_message_id = query.message.message_id
        last_chat_id = query.message.chat_id
        
        term.start_real_terminal()
        
        threading.Thread(target=term.get_stdout_real_terminal).start()
        threading.Thread(target=refresh_stdout_on_telegram).start()
    
    elif mode == 's': # stop real terminal
        old_text = term.text_stdout
        
        term.close_real_terminal()
        
        bot.edit_message_text(chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              text=old_text)
        
        reply_markup = InlineKeyboardMarkup(term.create_keyboard())
        bot.send_message(chat_id=query.message.chat_id,
                    text="current directory: \n{}".format(term.current_dir),
                    reply_markup=reply_markup)


def communicate(bot, update):
    global last_message_id
    if not term.is_started_real_terminal:
        update.message.reply_text("Terminal is not running")
    else:
        term.send_stdin_real_terminal(update.message.text)


def shutdown():
    updater.stop()
    updater.is_idle = False

def stop(bot, update):
    logger.info("from {}: /stop".format(update.message.chat_id))
    if update.message.chat_id not in ADMINS:
        update.message.reply_text("You aren't an admin!")
        
        for id_ in ADMINS: # Warning to the admins
            bot.send_message(chat_id=id_, text="{} attempted to shutdown".format(update.message.chat_id))
        return
    
    for id_ in ADMINS:
        bot.send_message(chat_id=id_, text="shutdown...")
    term.close_real_terminal()
    threading.Thread(target=shutdown).start()


updater = Updater(token=BOT_TOKEN)

updater.dispatcher.add_handler(MessageHandler(Filters.text, communicate))
updater.dispatcher.add_handler(CommandHandler('start', start))
updater.dispatcher.add_handler(CommandHandler('stop', stop))
updater.dispatcher.add_handler(CallbackQueryHandler(callback))

updater.start_polling()
updater.idle()
