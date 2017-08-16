#!/bin/python
import re, socket, time, sys, random, json, pickle


class goblinbot:
    def processCommand(self,sender,command, badges):
        part = command.split(" ")

        if not hasattr(self,'permissions') and command[1] == "!":
            return "permissions have not been configured"
        badges.append("global")
        myPermissions = []

        allowed = []
        for level in self.permissions.keys():
            if part[0].lower() in self.permissions[level]:
                allowed.append(level)
        permitted = False
        for badge in badges:
            if badge in allowed:
                permitted = True
        if len(allowed)> 0 and not permitted:
            return "The "+part[0]+" command can only be used by the following user types: "+(",".join(allowed))


        if part[0] == "!help":
            available = ["!help","!roll","!vote","!results","!subname","!listnames","!randomname"]
            if hasattr(self,'commands'):
                for command in self.commands.keys:
                    available.append(command)

        if part[0] == "!subname":
            if not hasattr(self,'namelists'):
                return "No namelists are configured"
            if len(part)<3:
                return "Not enough arguments. Please enter !getname game("+(', '.join(self.namelists))+") yoursuggestion"
            if part[1].upper() not in self.namelists:
                return "Name list invalid. Please enter !subname game("+(', '.join(self.namelists))+") yoursuggestion"
            if part[1].upper() not in self.names:
                self.names[part[1].upper()] = []
            self.names[part[1].upper()].append(" ".join(part[2:]))
            #save the updated list
            pickle.dump(self.names, open("pickles/names.pickle", "wb"))
            return "Your name "+part[2]+" has been submitted to the "+part[1]+" namelist."

        if part[0] == "!listnames":
            if not hasattr(self,'namelists'):
                return "No namelists are configured"
            if len(part)<2:
                return "Not enough arguments. Please enter !getname game("+(', '.join(self.namelists))+")"
            if part[1].upper() not in self.namelists:
                return "Name list invalid. Please enter !getname game("+(', '.join(self.namelists))+")"
            if part[1].upper() not in self.names or len(self.names[part[1].upper()])<1:
                return "No names for that list"
            return ', '.join(self.names[part[1].upper()])+"\r\n"

        if part[0] == "!randomname":
            if not hasattr(self,'namelists'):
                return "No namelists are configured"
            if len(part)<2:
                return "Not enough arguments. Please enter !getname game("+(', '.join(self.namelists))+")"
            if part[1].upper() not in self.namelists:
                return "Name list invalid. Please enter !getname game("+(', '.join(self.namelists))+")"
            if part[1].upper() not in self.names or len(self.names[part[1].upper()])<1:
                return "No names for that list"
            return random.choice(self.names[part[1].upper()])


        if part[0] == "!roll":
            if len(part) < 2:
                return "Not enough arguments. Please enter !roll rollcode(1d6, 2d4+1, etc)"
            for part in part[1:]:
                match = re.match("([0-9]+)[Dd]([0-9]+)([+\-][0-9]+)?",part)
                if not match:
                    return "rollcode must be in the format 1d1+1"
                else:
                    total = 0
                    output = []
                    for i in range(int(match.group(1))):
                        roll = random.randint(1,int(match.group(2))+1)
                        output.append(str(roll))
                        total += roll
                    if match.group(3) is not None:
                        if match.group(3)[0] == "+":
                            output.append(match.group(3))
                            total += int(match.group(3)[1:])
                        if match.group(3)[0] == "-":
                            output.append(match.group(3))
                            total -= int(match.group(3)[1:])
                    return sender+" rolled "+(", ".join(output))+" = "+str(total)

        if part[0] == "!vote":
            if not hasattr(self,'polls'):
                return "No polls are configured"
            if len(part) < 3:
                return "Not enough arguments. Please enter !vote pollname option"
            if part[1].lower() not in self.polls:
                return "There is no poll called "+part[1]+" available polls:"+(", ".join(self.polls))
            #allow for either vote options that are from a specified list or freeform
            if self.polls[part[1].lower()] != "*" and part[2].lower() not in self.polls[part[1].lower()]:
                return "The poll "+part[1]+" does not allow the option "+part[2]+". Options are:"+(", ".join(self.polls[part[1].lower()]))
            #build the structure if it's not already there
            if self.votes == None:
                self.votes = {}
            if part[1].lower() not in self.votes:
                self.votes[part[1].lower()] = {}
            if part[2].lower() not in self.votes[part[1].lower()]:
                self.votes[part[1].lower()][part[2].lower()] = []
            #remove their vote from any existing options
            for option in self.votes[part[1].lower()]:
                if sender in self.votes[part[1].lower()][option]:
                    self.votes[part[1].lower()][option].remove(sender)
            #put their vote in their new choice
            self.votes[part[1].lower()][part[2].lower()].append(sender)
            return sender+" voted for "+part[1].lower()+": "+part[2].lower()

        if part[0] == "!results":
            if not hasattr(self,'polls'):
                return "No polls are configured"
            if not hasattr(self,'votes'):
                return "No votes have been submitted"
            if len(part) <2:
                return "Not enough arguments. Please enter !results pollname. available polls:"+(", ".join(self.polls))
            if part[1].lower() not in self.polls:
                return part[1].lower()+" is not a current poll"
            if part[1].lower() not in self.votes:
                return part[1].lower()+" has no submitted votes"
            output = []
            for option in self.votes[part[1].lower()].keys():
                output.append(option+": "+str(len(self.votes[part[1].lower()][option])))
            return "\r\n".join(output)

        if part[0] == "!reload":
            self.loadConfig()
            return "reloaded"

            #This just returns whatever is listed against the command in the json
        if hasattr(self,'commands') and part[0].lower() in self.commands:
            return self.commands[part[0]]


    def send(self,message):
        if message is None:
            print "MESSAGE WAS NONE"
            return
        print "SENDING:"+message
        self.irc.send(("PRIVMSG "+self.channel+" : "+message+" \r\n").encode("utf-8"))


    def loadConfig(self):
        json_data=open("config.json").read()
        config = json.loads(json_data)
        self.name = config['name']
        self.password = config['oauth']
        self.channel = config['channel']

        if 'namelists' in config:
            self.namelists = config['namelists']
        if 'customcommands' in config:
            self.commands = config['customcommands']
        if 'polls' in config:
            self.polls = config['polls']
        if 'permissions' in config:
            self.permissions = config['permissions']

    def main(self):
        self.waitinglist = []
        self.loadConfig()
        self.votes = {}

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
                        breakup = re.split('^(@badges=.*?;)?.*?:(.*?)!.*?PRIVMSG (.*?) :(.*?)$',line)
                        for index, item in enumerate(breakup):
                            print index, item

                        if len(breakup) > 1:
                            if breakup[3] != self.name:
                                w = breakup[3]
                            elif breakup[2] != "":
                                w = "twitchpm"

                            namesplit = [self.name[0:i].lower() for i in range(3, len(self.name) + 1)]
                            bwo = breakup[4].lstrip()

                            sender = breakup[2]
                            badges = []
                            if breakup[1] is not None:
                                badges = breakup[1][8:].split(",")
                            for badge in range(0,len(badges)):
                                badges[badge] = re.sub("/[0-9]+;?$","",badges[badge])

                            breakupsplit = re.split("(, |: )",bwo,1)
                            bettersplit = re.match("^([^ ]+) ?(, |: )(.+)$",bwo)

                            words = "".join(breakupsplit)
                            if breakupsplit[0].strip().lower() in namesplit:
                                words = "".join(breakupsplit[2:])
                            if breakupsplit[-1][-1] in ["?","!","."] and breakupsplit[-1].strip().lower()[:-2] in namesplit and len(breakupsplit)>=2:
                                breakupsplit[-2] +=breakupsplit[-1][-1]
                                breakupsplit[-1] = breakupsplit[-1][:-2]
                            if breakupsplit[-1].strip().lower() in namesplit:
                                words = "".join(breakupsplit[:-2])

                            #Here's where we actually send the command off to be processed
                            if words[0]=="!":
                                self.send(self.processCommand(sender,words,badges))

                        if line.find("hostname") != -1:
                            self.irc.send ( 'JOIN '+self.channel+'\r\n'.encode("utf-8"))
                        if line.find("GLHF") != -1:
                            self.irc.send ( 'CAP REQ :twitch.tv/membership\r\n'.encode("utf-8"))
                            self.irc.send ( 'CAP REQ :twitch.tv/tags\r\n'.encode("utf-8"))
                        if line.find("his nickname is registered") != -1:
                            self.irc.send ( 'PRIVMSG NickServ : identify lovessocks\r\n'.encode("utf-8") )
                        if line.find("ou have not registered") != -1:
                            stayalive = False
                        if line.find("ERROR :Closing Link: ") != -1:
                            stayalive = False
                            time.sleep(6)
                        if line.find ( 'PING' ) != -1:
                            response = 'PONG ' + line.split() [ 1 ] + '\r\n'.encode("utf-8")
                            self.irc.send ( response )
                            print "pinged"
                            print "responded:"+response
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
