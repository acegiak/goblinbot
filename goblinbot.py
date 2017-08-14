#!/bin/python
import re, socket, time, sys, random, json, pickle


class goblinbot:
    def processCommand(self,sender,command):
        part = command.split(" ")
        if part[0] == "!subname":
            if len(part)<3:
                self.send("Not enough arguments. Please enter !getname game(AW,NMS,DD) yoursuggestion")
                return
            if part[1].upper() not in ['AW','NMS','DD']:
                self.send("Name list invalid. Please enter !subname game(AW,NMS,DD) yoursuggestion")
                return

            if part[1].upper() not in self.names:
                self.names[part[1].upper()] = []
            self.names[part[1].upper()].append(part[2])
            self.send("Your name "+part[2]+" has been submitted to the "+part[1]+" namelist.")
        if part[0] == "!getname":
            if len(part)<2:
                self.send("Not enough arguments. Please enter !getname game(AW,NMS,DD)")
                return
            if part[1].upper() not in ['AW','NMS','DD']:
                self.send("Name list invalid. Please enter !getname game(AW,NMS,DD)")
                return
            if part[1].upper() not in self.names or len(self.names[part[1].upper()])<1:
                self.send("No names for that list")
                return
            self.send(', '.join(self.names[part[1].upper()])+"\r\n")

        pickle.dump(self.names, open("pickles/names.pickle", "wb"))



    def send(self,message):
        self.irc.send(('PRIVMSG '+self.channel+' : '+message+" \r\n").encode("utf-8"))
    
    def main(self):
        self.waitinglist = []
        json_data=open("credentials.json").read()
        creds = json.loads(json_data)
        self.name = creds['name']
        self.password = creds['oauth']
        self.channel = creds['channel']

        try:
            self.names = pickle.load(open("pickles/names.pickle", "rb"))
        except (OSError, IOError) as e:
            self.names = {}
            pickle.dump(self.names, open("pickles/names.pickle", "wb"))



        self.network = "irc.chat.twitch.tv"
        print "running twitch thread"
        stripper = re.compile("\x03(?:\d{1,2}(?:,\d{1,2})?)?", re.UNICODE)
        while True:
            try:
                print "starting TWITCH self.irc connection"
                port = 6667
                pingeth = time.time()
                talklevel = 2

                self.irc = socket.socket ( socket.AF_INET, socket.SOCK_STREAM )
                self.irc.connect ( ( self.network, port ) )


                self.irc.send("PASS {}\r\n".format(self.password).encode("utf-8"))
                self.irc.send("NICK {}\r\n".format(self.name).encode("utf-8"))
                self.irc.send("JOIN {}\r\n".format(self.channel).encode("utf-8"))

                stayalive = True
                readbuffer=""
                while True:
                    readbuffer=readbuffer+self.irc.recv(64).encode("utf-8")
                    temp=readbuffer.split("\n")
                    readbuffer=temp.pop( )
                    for line in temp:
                        print "TWITCH data in:"+line
                        line=stripper.sub("",line.rstrip())

                        if(line[0]=="PING"):
                            s.send("PONG %s\r\n" % line[1].encode("utf-8"))
                        breakup = re.split('^:(.*?)!.*?PRIVMSG (.*?) :(.*?)$',line)
                        for index, item in enumerate(breakup):
                            print index, item

                        if len(breakup) > 1:
                            if breakup[2] != self.name:
                                w = breakup[2]
                            elif breakup[1] != "":
                                w = "twitchpm"
                            if re.search('who.*?daft', breakup[3]):
                                self.daft.say("I am daft",w,"twitch")
                            if re.search('[Nn]ick[nN]ame', breakup[3]):
                                self.daft.say("identify socks","Nickserv","twitch")
                                print "identifying"

                            namesplit = [self.name[0:i].lower() for i in range(3, len(self.name) + 1)]
                            bwo = re.sub('^<.*?> ',"",breakup[3].lstrip())
                            bridgename = re.match('^<(.*?)> ',breakup[3].lstrip())
                            if bridgename != None:
                                if 'players' in self.daft.modules.keys():
                                    self.daft.modules['players'].logon(bridgename.group(1),breakup[1])
                                print "sender is now "+bridgename.group(1)
                                w = breakup[1]+w
                                sender = bridgename.group(1)
                            else:
                                sender = breakup[1]
                            if re.match('^[\.]+\r\n?$', breakup[3]):
                                self.daft.boom("AWKWARD",sender,w)
                            if re.match('^[Bb]otsnack\r\n?$', breakup[3]):
                                self.daft.boom("botsnack",sender,w)
                            breakupsplit = re.split("(, |: )",bwo,1)
                            bettersplit = re.match("^([^ ]+) ?(, |: )(.+)$",bwo)
                            ct = int(0.6+((time.time() - pingeth)/talklevel))
                            if ct < 1:
                                ct = 1
                            words = "".join(breakupsplit)
                            if breakupsplit[0].strip().lower() in namesplit:
                                words = "".join(breakupsplit[2:])
                            if breakupsplit[-1][-1] in ["?","!","."] and breakupsplit[-1].strip().lower()[:-2] in namesplit and len(breakupsplit)>=2:
                                breakupsplit[-2] +=breakupsplit[-1][-1]
                                breakupsplit[-1] = breakupsplit[-1][:-2]
                            if breakupsplit[-1].strip().lower() in namesplit:
                                words = "".join(breakupsplit[:-2])

                            if words[0]=="!":
                                self.processCommand(sender,words)
                        if line.find("hostname") != -1:
                            self.irc.send ( 'JOIN '+self.channel+'\r\n'.encode("utf-8"))
                        if line.find("his nickname is registered") != -1:
                            self.irc.send ( 'PRIVMSG NickServ : identify lovessocks\r\n'.encode("utf-8") )
                        if line.find("ou have not registered") != -1:
                            stayalive = False
                        if line.find("ERROR :Closing Link: ") != -1:
                            stayalive = False
                            time.sleep(6)
                        if line.find ( 'PING' ) != -1:
                            self.irc.send ( 'PONG ' + line.split() [ 1 ] + '\r\n'.encode("utf-8") )
                            print "pinged"
                        if line.find ( 'KICK' ) != -1:
                            self.irc.send ( 'JOIN '+self.channel+'\r\n'.encode("utf-8") )
                        if(len(self.waitinglist) > 0):
                            for waitingmessage in self.waitinglist:
                                self.irc.send(waitingmessage.encode("utf-8"))
                                print "Send: "+waitingmessage
                            self.waitinglist = []
                self.irc.close()
            except socket.timeout:
                print("timeout error")
            except socket.error:
                print("socket error occured: ")
                print sys.exc_info()[0]

if __name__ == '__main__':
    goblinbot().main()



def signal_handler(signal, frame):
    print("Ctrl+C captured in driver!")
    sys.exit()

signal.signal(signal.SIGINT, signal_handler)
