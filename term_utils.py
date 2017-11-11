import os
import socket
from time import sleep
from shlex import quote
from select import select
from subprocess import Popen, PIPE

from telegram import InlineKeyboardButton

def check_file(f): # check the file name...
    if not 0 < len(f) < 64: # string empty or too long (callback_data can hold up to 64 bytes)
        return False
        
    if f.endswith('~'): # for some reasons backup files raise an telegram error...
        return False
    
    return True

def build_menu(buttons, header=None, footer=None):
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
        self.is_started_real_terminal = False
    
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
        self.files.insert(0, [InlineKeyboardButton('OPEN TERMINAL HERE',
                                                           callback_data=' t')])
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
        
    def start_real_terminal(self):
        stdout_bot = socket.socket()
        stdout_bot.bind(("localhost", 3300))
        stdout_bot.listen(1)
        
        # only at this point i can start the real_terminal, because stdout_bot 
        # socket is read to receive connections
        os.system("""cd {} ; gnome-terminal -e 'bash -c "python3 {}/real_terminal.py"'""".format(
                                                 self.current_dir, os.getcwd()))

        stdout, addr = stdout_bot.accept()

        sleep(0.1)
        stdin = socket.socket()
        stdin.connect(("localhost", 3301))

        sleep(0.1)
        shutdown = socket.socket()
        shutdown.connect(("localhost", 3302))
        
        self.stdout = stdout # stdout from terminal to telegram
        self.stdin = stdin # stdin from telegram to terminal
        self.shutdown = shutdown # shutdown terminal command
        
        self.__stdout_bot = stdout_bot # i need this only in close_real_terminal
        
        self.text_stdout = '' # this contains the text of the terminal
        self.stop_read_stdout = False
        
        self.is_started_real_terminal = True
    
    
    def send_stdin_real_terminal(self, text):
        """
        Special sequences...
        $tabs$   -> 4 spaces
        $tab$    -> tab
        $nl$     -> new line '\n'
        $!nl$    -> not new line (works at the end of the text)
        $ctrl-z$ -> send ctrl-z
        $ctrl-c$ -> send ctrl-c
        """
        text = text.replace('$tabs$', '    ') # tab (4 spaces)
        text = text.replace('$tab$', '	') # tab
        text = text.replace('$nl$', '\n') # new line
        text = text.replace('$ctrl-z$', '\x1a$!nl$') # ctrl-z (not newline)
        text = text.replace('$ctrl-c$', '\x03$!nl$') # ctrl-c (not newline)
        # TODO add others...
        if not text.endswith('\n') and not text.endswith('$!nl$'): 
            text += '\n'
        text = text.replace('$!nl$', '') # remove no newlines
        self.stdin.sendall(text.encode('utf-8'))
    
    	
    def get_stdout_real_terminal(self):
        """ refresh the self.text_stdout when there is an output in stdout 
        this method need a new thread """
        STDOUT_FILENO = self.stdout.fileno()
        fds = [STDOUT_FILENO]
        while True:
            select(fds, [], [])
            if self.stop_read_stdout:
                break
            
            new_text = self.stdout.recv(4096).decode('utf-8').replace('\r\n', '\n')
            
            if '\x08' in new_text: # cancel one char
                self.text_stdout = self.text_stdout[:-1]
            elif '\x07' in new_text:
                pass # nothing to delete...
            else:
                self.text_stdout += new_text
    
    
    def close_real_terminal(self):
        if not self.is_started_real_terminal: return # if is already closed
        self.is_started_real_terminal = False
        
        # this two lines serve the get_stdout_real_terminal methon
        self.stop_read_stdout = True
        self.send_stdin_real_terminal('goodbye')
        sleep(0.1)
        
        # shutdown real terminal
        self.shutdown.send(b' ')
        
        # close all sockets
        self.stdout.close()
        self.stdin.close()
        self.shutdown.close()
        self.__stdout_bot.close()
        
        self.stop_read_stdout = False
        self.text_stdout = []

