""" Actually this is a modified version of the builtin 'pty' module """

import re
import os
import tty
import socket
from select import select
from pty import (STDIN_FILENO, STDOUT_FILENO, STDERR_FILENO, CHILD, fork, 
                 _writen, _read)

# send terminal stdout to telegram
stdout_bot = socket.socket()
stdout_bot.connect(("localhost", 3300))

# read telegram messages
stdin_bot = socket.socket()
stdin_bot.bind(("localhost", 3301))
stdin_bot.listen(1)
conn_stdin, addr = stdin_bot.accept()
STDIN_BOT_FILENO = conn_stdin.fileno()

# shutdown signal
shutdown = socket.socket()
shutdown.bind(("localhost", 3302))
shutdown.listen(1)
conn_shutdown, addr = shutdown.accept()
SHUTDOWN_FILENO = conn_shutdown.fileno()


def escape_ansi(line):
    """ remove ansi colors and others escape sequences... """
    ansi_escape = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]')
    line = ansi_escape.sub('', line.decode('utf-8'))
    
    #delete all chars between \x1b and \x07
    target_replace = re.search(r'(\x1b)(.*?)(\x07)', line)
    target_replace = target_replace.group(0) if target_replace is not None else '' 
    return line.replace(target_replace, '').encode('utf-8')


def _copy(master_fd, master_read=_read, stdin_read=_read):
    """Parent copy loop.
    
            pty master -> standard output   (master_read)
            pty master -> telegram output   (stdout_bot.sendall)
            standard input -> pty master    (stdin_read)
            telegram input -> pty master    (conn_stdin.recv)"""
    fds = [master_fd, STDIN_FILENO, STDIN_BOT_FILENO, SHUTDOWN_FILENO]
    
    while True:
        rfds, wfds, xfds = select(fds, [], [])
        if master_fd in rfds:
            data = master_read(master_fd)
            if not data:  # Reached EOF.
                fds.remove(master_fd)
            else:
                os.write(STDOUT_FILENO, data)
                stdout_bot.sendall(escape_ansi(data)) # send output to telegram
                
        if STDIN_FILENO in rfds:
            data = stdin_read(STDIN_FILENO)
            if not data:
                fds.remove(STDIN_FILENO)
            else:
                _writen(master_fd, data)
                
        if STDIN_BOT_FILENO in rfds: 
            data = conn_stdin.recv(4096) # read from telegram
            _writen(master_fd, data)
            
        if SHUTDOWN_FILENO in rfds:
           break


def spawn(argv, master_read=_read, stdin_read=_read):
    """Create a spawned process."""
    if type(argv) == type(''):
        argv = (argv,)
    pid, master_fd = fork()
    if pid == CHILD:
        os.execlp(argv[0], *argv)
    try:
        mode = tty.tcgetattr(STDIN_FILENO)
        tty.setraw(STDIN_FILENO)
        restore = 1
    except tty.error:    # This is the same as termios.error
        restore = 0
    try:
        _copy(master_fd, master_read, stdin_read)
    except OSError:
        if restore:
            tty.tcsetattr(STDIN_FILENO, tty.TCSAFLUSH, mode)

    os.close(master_fd)


if __name__ == '__main__':
    try:
        spawn("/bin/bash")
    finally:
        conn_shutdown.close()
        conn_stdin.close()
        stdout_bot.close()
        stdin_bot.close()
        shutdown.close()
