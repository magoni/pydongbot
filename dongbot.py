import socket
import threading

IRC_PORT = 6667
SERVER = 'esm41.com'
BANNER_END = '' # the last packet in the server's welcome banner

class IRCBot:
    def __init__(self,
                 nick="mybot",
                 user='',
                 server=SERVER,
                 channels=[])
        self.nick = nick
        
        if user:
            self.user = user
        else:
            self.user = self.nick

        self.host = socket.gethostname()
        self.server = server
        self.channels = channels

        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self):
        self.s.connect(self.server, IRC_PORT)
        self.s.send('NICK %s\r\n' % (self.nick,))
        self.s.send('USER %s %s %s :%s\r\n' % (self.user,
                                               self.host,
                                               self.server,
                                               self.user))
        while 1:
            message = self.s.recv(1024)
            print message
            if message == BANNER_END:
                break

        # at this point, you need to do your identifying and shit

        for c in self.channels:
            self.s.send('JOIN ' + c + '\r\n')

        # main loop

        while 1:
            packet = self.s.recv(1024)
            packet.replace('\n\r', '\r\n')
            packets = packet.split('\r\n')[:-1]
            for p in packets:
                self.handle(p)

    def handle(self, message):
        print message
        if message.startswith('PING :'):
            server = message[len('PING'):]
            self.s.send('PONG%s\r\n' % (server,))
    
    def send_message(self, channel, message):
        self.s.send('PRIVMSG %s :%s\r\n' % (channel, message))

    def send_action(self, channel, action):
        self.s.send('PRIVMSG %s :\x01ACTION %s\x01\r\n' % (channel, action))

    def irc_quit(self, message):
        self.s.send('QUIT :%s\r\n' % (message,))
        self.s.close()
