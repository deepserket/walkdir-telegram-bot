import os
from shlex import quote
from subprocess import Popen, PIPE

from telegram import InlineKeyboardButton

def check_file(f): # check the file name...
    if not 0 < len(f) < 64: # string empty or too long (callback_data can hold up to 64 bytes)
        return False
        
    if f.endswith('~'): # for some reasons backup files raise an telegram error...
        return False
    
    return True

def build_menu(buttons, header=None, footer=None): # stoled from https://github.com/Endogen/Telegram-Kraken-Bot/blob/master/telegram_kraken_bot.py
    menu = buttons

    if header:
        menu.insert(0, [header])
    if footer:
        menu.append([footer])

    return menu


class Terminal:
    
    def __init__(self, start_dir):
        self.start_dir = start_dir
        self.current_dir = start_dir
        self.files = [] # files and directiries in current_dir
    
    def cd(self, dir_name=None):
        """ if dir_name is None move to start_dir, else change directory """
        if dir_name is None:
            dir_name = self.start_dir
        
        p = Popen('cd {} ; pwd'.format(quote(dir_name)), cwd=self.current_dir, shell=True, stdout=PIPE, stderr=PIPE).communicate()
        
        out = str(p[0], 'utf-8')
        self.current_dir = out.split('\n')[-2]
    
    def ls(self):
        """ Generate a list of InlineKeyboardButton of files and dir in current_dir """
        p = Popen('ls', cwd=self.current_dir, shell=True, stdout=PIPE, stderr=PIPE).communicate()
        
        files = str(p[0], 'utf-8').strip().split('\n') # Also contains directories
        files = [f for f in files if check_file(f)] # removing bad files...
        
        kb = []

        if self.current_dir != '/':
            kb.append([InlineKeyboardButton("..", callback_data='..d')])
            
        for f in files: # First the directories...
            path = os.path.join(self.current_dir, f)
            if os.path.isdir(path):
                kb.append([InlineKeyboardButton("dir: {}".format(f),
                            callback_data="{}d".format(f))])
            
        for f in files: # ...Then the files
            path = os.path.join(self.current_dir, f)
            if os.path.isfile(path):
                kb.append([InlineKeyboardButton("file: {}".format(f),
                            callback_data="{}f".format(f))])
        return kb
    
    def create_keyboard(self, window=0):
        self.files = self.ls()
        
        if len(self.files) <= 52:
            return self.files
        
        start = 0 if window == 0 else window * 50
        stop = start + 50
        
        head = None if start == 0 else (InlineKeyboardButton("<<<PREVIOUS<<<",
                                          callback_data="{}w".format(window-1)))
                                           
        foot = None if stop > len(self.files) else (InlineKeyboardButton(">>>NEXT>>>",
                                          callback_data="{}w".format(window+1)))
        
        kb = build_menu(self.files[start:stop], header=head, footer=foot)
        return kb
        


# working in progress...
'''
    def execute(self, cmd): 
        """ exec a cmd without side effects (like changing current_dir, etc...)"""
        p = Popen(cmd, cwd=self.current_dir, shell=True, stdout=PIPE, stderr=PIPE).communicate()
        
        return str(p[0], 'utf-8').strip()
'''

