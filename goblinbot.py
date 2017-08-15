#!/bin/python
import re, socket, time, sys, random, json, pickle


class goblinbot:
    def processCommand(self,sender,command):
        part = command.split(" ")
        if part[0] == "!subname":
            if len(part)<3:
                return "Not enough arguments. Please enter !getname game("+(', '.join(self.namelists))+") yoursuggestion"

            if part[1].upper() not in self.namelists:
                return "Name list invalid. Please enter !subname game("+(', '.join(self.namelists))+") yoursuggestion"
            if part[1].upper() not in self.names:
                self.names[part[1].upper()] = []
            self.names[part[1].upper()].append(" ".join(part[2:]))
            return "Your name "+part[2]+" has been submitted to the "+part[1]+" namelist."

        if part[0] == "!listnames":
            if len(part)<2:
                return "Not enough arguments. Please enter !getname game("+(', '.join(self.namelists))+")"
            if part[1].upper() not in self.namelists:
                return "Name list invalid. Please enter !getname game("+(', '.join(self.namelists))+")"
            if part[1].upper() not in self.names or len(self.names[part[1].upper()])<1:
                return "No names for that list"
            self.send(', '.join(self.names[part[1].upper()])+"\r\n")

        if part[0] == "!randomname":
            if len(part)<2:
                return "Not enough arguments. Please enter !getname game("+(', '.join(self.namelists))+")"
            if part[1].upper() not in self.namelists:
                return "Name list invalid. Please enter !getname game("+(', '.join(self.namelists))+")"
            if part[1].upper() not in self.names or len(self.names[part[1].upper()])<1:
                return "No names for that list"
            self.send(random.choice(self.names[part[1].upper()])+"\r\n"))

        pickle.dump(self.names, open("pickles/names.pickle", "wb"))

        if part[0] == "!roll":
            if len(part) < 2:
                return "Not enough arguments. Please enter !roll rollcode(1d6, 2d4+1, etc)"
            for part in part[1:]:
                match = re.match("([0-9]+)[Dd]([0-9]+)([+\-][0-9]+)?")
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
                    return (", ".join(output))+" = "+str(total)

	if part[0] == "!vote":
		if len(part) < 3:
			return "Not enough arguments. Please enter !vote pollname option"
		if part[1].lower() not in self.polls:
			return "There is no poll called "+part[1]
		#allow for either vote options that are from a specified list or freeform
		if self.polls[part[1].lower()] != "*" and part[2].lower() not in self.polls[part[1].lower()]:
			return "The poll "+part[1]+" does not allow the option "+part[2]+". Options are:"+(", ".join(self.polls[part[1].lower()]))
		#build the structure if it's not already there
		if part[1].lower() not in self.votes:
			self.votes[part[1].lower()] = {}
		if part[2].lower() not in self.votes[part[1].lower()]:
			self.votes[part[1].lower()][part[2].lower()] = []
		#remove their vote from any existing options
		for option in self.votes[part[1].lower()]:
			option.remove(sender)
		#put their vote in their new choice
		self.votes[part[1].lower()][part[2].lower()].append(sender)

	if part[0] == "!results":
		output = []
		if part[1].lower() not in self.votes:
                        self.votes[part[1].lower()] = {}
		for option in self.votes[part[1].lower()].keys():
                        output.append(option+": "+str(len(self.votes[part[1].lower()][option])))
		return "\r\n".join(output)

        #This just returns whatever is listed against the command in the json
        if part[0] in self.commands:
            return self.commands[part[0]]


    def send(self,message):
        self.irc.send(('PRIVMSG '+self.channel+' : '+message+" \r\n").encode("utf-8"))

    def main(self):
        self.waitinglist = []
        json_data=open("credentials.json").read()
        creds = json.loads(json_data)
        self.name = creds['name']
        self.password = creds['oauth']
        self.channel = creds['channel']

        self.namelists = creds['namelists']
        self.commands = creds['commands']
        self.polls = creds['polls']
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
                        breakup = re.split('^:(.*?)!.*?PRIVMSG (.*?) :(.*?)$',line)
                        for index, item in enumerate(breakup):
                            print index, item

                        if len(breakup) > 1:
                            if breakup[2] != self.name:
                                w = breakup[2]
                            elif breakup[1] != "":
                                w = "twitchpm"

                            namesplit = [self.name[0:i].lower() for i in range(3, len(self.name) + 1)]
                            bwo = breakup[3].lstrip()

                            sender = breakup[1]

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
                                self.send(self.processCommand(sender,words))

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
