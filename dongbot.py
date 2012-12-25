import socket
import threading
import re
import pickle
import os.path

IRC_PORT = 6667
SERVER = 'esm41.com'
REMEMBER_BACKUP = "remember_dict.bkp"
REMEMBER_OBJ = re.compile(r"!remember (.*)>(.*)")
FORGET_OBJ = re.compile(r"!forget (.*)")
CHAN_MESSAGE = re.compile(r":(\w+)!.*PRIVMSG #(\w+) :(.*)")

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
        # load the backup of remembered words if it exists
        if os.path.isfile(REMEMBER_BACKUP):
            self.remembered = pickle.load(open(REMEMBER_BACKUP, 'rb'))
        else:
            self.remembered = {}

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
            pong_str = 'PONG%s\r\n' % (server,)
            print pong_str
            self.s.send(pong_str)
        elif chan_message:
            #this should end up being refactored at some point in time
            speaker = chan_message.groups()[0]
            channel = chan_message.groups()[1]
            msg = chan_message.groups()[2].strip()
            rem_object = REMEMBER_OBJ.search(msg)
            for_object = FORGET_OBJ.search(msg)

            if msg == "!help":
                self.send_message("#" + channel, "!remember KEY>VALUE")
                self.send_message("#" + channel, "!forget KEY")
               # self.send_message("#" + channel, "!history")
                self.send_message("#" + channel, "!help")
                self.send_message("#" + channel, "!help COMMAND")
            #elif msg=="!backup":
            #    pickle.dump(self.remembered, open(REMEMBER_BACKUP, 'wb'))
            #    self.send_message("#" + channel, "words backed up.")
            elif msg.startswith('!help'):
                commands = {"remember":"remembers a KEY so that whenever it is said, VALUE is replied.",
                            "forget":"forgets a KEY that had been remembered.",
                            "history":"displays recorded history",
                            "histlast":"displays last NUM recorded messages",
                            "log":"starts logging messages",
                            "pauselog":"pauses the logging of messages",
                            "destroylog":"destroys all logs of messages",
                            "help":"gives help"}
                cmd = msg[5:].strip()
                if cmd[0] == "!":
                    cmd = cmd[1:]
                if cmd in commands:
                    self.send_message("#" + channel, commands[cmd])
                else:
                    self.send_message("#" + channel, "Not a valid command.")

            if rem_object:
                groups = rem_object.groups()
                self.remembered[groups[0].strip()] = groups[1].strip()
                # backup when word is added
                pickle.dump(self.remembered, open(REMEMBER_BACKUP, 'wb'))
                self.send_action("#" + channel, "remembered \"%s\"" %
                             (groups[0].strip(),))
            elif for_object:
                groups = for_object.groups()
                self.remembered.pop(groups[0].strip())
                # back up when word is removed
                pickle.dump(self.remembered, open(REMEMBER_BACKUP, 'wb'))
                self.send_action("#" + channel, "forgot \"%s\"" %
                             (groups[0].strip(),))
            else:
                for key in self.remembered:
                    if re.search('\\b' + re.escape(key) + '\\b', msg):
                        self.send_message("#" + channel, self.remembered[key])

    def send_message(self, channel, message):
        self.s.send('PRIVMSG %s :%s\r\n' % (channel, message))

    def send_action(self, channel, action):
        self.s.send('PRIVMSG %s :\x01ACTION %s\x01\r\n' % (channel, action))

    def irc_quit(self, message):
        self.s.send('QUIT :%s\r\n' % (message,))
        self.s.close()

if "__main__" == __name__:

    bot = IRCBot("dongbot5000", 'lol', SERVER, ['#main'])
    bot.start()
