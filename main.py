import os
import logging
import threading

from telegram import InlineKeyboardMarkup
from telegram.ext import Updater, CallbackQueryHandler, MessageHandler, Filters, CommandHandler

from term_utils import Terminal

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)

with open("SECRETS.txt", "r") as f:
    ADMINS = [int(n) for n in f.readline().strip().split(',')]
    BOT_TOKEN = f.readline().strip()
    
    START_DIR = f.readline().strip()
    if not START_DIR:
        START_DIR = os.getcwd()

term = Terminal(START_DIR)

logger.info("Starting the bot... send me a /start command!")
    

def start(bot, update):
    logger.info("from {}: /start".format(update.message.chat_id))

    if update.message.chat_id not in ADMINS:
        update.message.reply_text("You aren't an admin!")
        
        for id_ in ADMINS: # Warning to the admins
            bot.send_message(chat_id=id_, text="{} attempted to access".format(update.message.chat_id))
        return
    
    term.current_dir = term.start_dir
    reply_markup = InlineKeyboardMarkup(term.ls())
    update.message.reply_text(term.current_dir, reply_markup=reply_markup)


def callback(bot, update):
    query = update.callback_query
    
    if query.message.chat_id not in ADMINS:
        return # without this the bot can be craked: https://github.com/python-telegram-bot/python-telegram-bot/issues/709
    
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
    
    threading.Thread(target=shutdown).start()


updater = Updater(token=BOT_TOKEN)

updater.dispatcher.add_handler(CommandHandler('start', start))
updater.dispatcher.add_handler(CommandHandler('stop', stop))
updater.dispatcher.add_handler(CallbackQueryHandler(callback))

updater.start_polling()
updater.idle()
