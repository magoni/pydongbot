import socket
import threading
import re

IRC_PORT = 6667
SERVER = 'esm41.com'
REMEMBER_OBJ = re.compile(r"remember:(.*)->(.*)")
FORGET_OBJ = re.compile(r"forget:(.*)")
CHAN_MESSAGE = re.compile(r"PRIVMSG #(\w+) :(.*)")
remembered = {}

class IRCBot:
    def __init__(self,
                 nick="mybot",
                 user='',
                 server=SERVER,
                 channels=[]):
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
        self.s.connect((self.server, IRC_PORT))
        self.s.send('NICK %s\r\n' % (self.nick,))
        self.s.send('USER %s %s %s :%s\r\n' % (self.user,
                                               self.host,
                                               self.server,
                                               self.user))
        while 1:
            message = self.s.recv(1024)
            print message
            if re.search("(.*)End of /MOTD command(.*)", message):
                break

        # identifying will happen eventually 
        for i in self.channels:
            self.s.send('JOIN ' + i + '\r\n')
            print 'joined ' + i

        # main loop
        while 1:
            packet = self.s.recv(1024)
            packet.replace('\n\r', '\r\n')
            packets = packet.split('\r\n')[:-1]
            for p in packets:
                self.handle(p)

    def handle(self, message):
        print message
        chan_message = CHAN_MESSAGE.search(message)
        if message.startswith('PING :'):
            server = message[len('PING'):]
            self.s.send('PONG%s\r\n' % (server,))
        elif chan_message:
            #this should end up being refactored at some point in time
            channel = chan_message.groups()[0]
            msg = chan_message.groups()[1]
            rem_object = REMEMBER_OBJ.search(msg)
            for_object = FORGET_OBJ.search(msg)
            if rem_object:
                groups = rem_object.groups()
                remembered[groups[0].strip()] = groups[1].strip()
                self.send_action("#" + channel, "remembered \"%s\"" %
                             (groups[0].strip(),))
            elif for_object:
                groups = for_object.groups()
                remembered.pop(groups[0].strip())
                self.send_action("#" + channel, "forgot \"%s\"" %
                             (groups[0].strip(),))
            else:
                for key in remembered:
                    if msg.find(key) != -1:
                        self.send_message("#" + channel, remembered[key])

    def send_message(self, channel, message):
        self.s.send('PRIVMSG %s :%s\r\n' % (channel, message))

    def send_action(self, channel, action):
        self.s.send('PRIVMSG %s :\x01ACTION %s\x01\r\n' % (channel, action))

    def irc_quit(self, message):
        self.s.send('QUIT :%s\r\n' % (message,))
        self.s.close()

if "__main__" == __name__:

    bot = IRCBot("pydongbot", 'lol', SERVER, ['#dongtest'])
    bot.start()
