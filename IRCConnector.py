import socket
from threading import Thread
import re
import requests
import json



class IRC:
    PONG = 808
    def __init__(self, HOST = "irc.chat.twitch.tv", PORT=6667, **kwargs):
        self.con = socket.socket()
        try:
            self.con.connect((HOST, PORT))
        except Exception as e:
            print(e)
        self.con.setblocking(False)
        self.con.settimeout(120)
        self.debugging = False
        for key, value in kwargs.items():
            if key == "debugging" and value == True:
                self.debugging = True
                print("Debugging enabled")

    def Login(self,OAuth = None, NICK = None, CHANNEL = None):
        PASSCMD = "PASS {}\r\n".format(OAuth)
        NICKCMD = "NICK {}\r\n".format(NICK)
        JOINCMD = "JOIN #{}\r\n".format(CHANNEL)
        self.con.send(bytes(PASSCMD, "UTF-8"))
        self.con.send(bytes(NICKCMD, "UTF-8"))
        self.con.send(bytes(JOINCMD, "UTF-8"))
        self.Channel = CHANNEL
        self.Nickname = NICK
        self.REGEX = "^:(\w+)!\w+@\w+.tmi.twitch.tv\s?(?:PRIVMSG)\s#(\w+)\s?:(.*)\r?\n?$"
        self.ChannelList = [CHANNEL]
        self.ChannelMetadata = {}

    def GetMessage(self, callback):
        MSG = ""
        self.MessageCallback = callback
        while True:
            try:
                MSG = self.con.recv(1024).decode('UTF-8')
                if self.debugging:
                    print(MSG)

                if len(MSG) > 0:
                    if MSG[0:4] == "PING":
                        self.SendPong()
                        continue
                    if MSG[0:7] != "PRIVMSG":
                        m = re.search(self.REGEX, str(MSG).strip("\r\n"))
                        if m != None:
                            callback(m.group(1), m.group(3), m.group(2))
                        else:
                            pass

            except socket.timeout as ex:
                pass
            except socket.error as ex:
                print(ex)
            except Exception as ex:
                print(ex)

    def OnMessage(self, callback):
        t = Thread(target=self.GetMessage, args=(callback,))
        t.start()
        self.RetrieveThread = t
        return t

    def Say(self, message, channel = None):
        if channel == None:
            self.con.send(bytes("PRIVMSG #{} :{}\r\n".format(self.Channel,message), "UTF-8"))
        else:
            self.con.send(bytes("PRIVMSG #{} :{}\r\n".format(channel,message), "UTF-8"))
        self.MessageCallback(self.Nickname, message, self.Channel)
    def Close(self):
        self.con.send(bytes("PART #{}\r\n".format(self.Channel), "UTF-8"))
        self.con.close()
    def Join(self, channel):
        self.con.send(bytes("JOIN #{}\r\n".format(channel), "UTF-8"))
        self.ChannelList.append(channel)
        self.Channel = channel
    def SendPong(self):
        self.con.send(bytes("PONG :tmi.twitch.tv\r\n", "UTF-8"))
    def ChangeChannel(self, channel):
        if channel in self.ChannelList:
            self.Channel = channel
    def Clearchat(self):
        self.Say("/clear")
    def GetInformation(self):
        r=requests.get("http://tmi.twitch.tv/group/user/{}/chatters".format(self.Channel))
        j = json.loads(r.text)
        if self.Channel not in self.ChannelMetadata:
            self.ChannelMetadata[self.Channel] = []
        for m in j["chatters"]["moderators"]:
            self.ChannelMetadata[self.Channel].append(m)