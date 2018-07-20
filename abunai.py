#! /usr/bin/env python
# Abunai v2.1
# an irc translation bot script
# call with python abunai.py server nick channel USER USERLANGUAGE CHANNELLANGUAGE
# do not include the # sign in the channel arg
# this script won't play nicely with servers that need nickserv as is
import sys
import socket
from threading import Thread
from textblob import TextBlob

# declare variables for where bot goes
try:
	HOST=sys.argv[1]
	PORT=6667
	NICK=sys.argv[2]
	IDENT=sys.argv[2]
	REALNAME=sys.argv[2]
	CHAN="#" + sys.argv[3]
	USER=sys.argv[4]
	userlang=sys.argv[5]
	chanlang=sys.argv[6]
except:
	print("invalid args")
	print("Usage: python abunai.py SERVER NICK CHANNEL USERNICK USERLANGUAGE CHANNELLANGUAGE")
	print("do not include the # in the channel name")
	exit()

# if you want to manually set the info...
#HOST=""
#PORT=6667
#NICK="Bot"
#IDENT="Bot"
#REALNAME="Bot"
#CHAN="#abu"

threads = []
msgqueue = []
PONG = False

def create_conn():
    # open connection to irc server
    s=socket.socket( )
    s.connect((HOST, PORT))
    s.send("NICK {}\r\n".format(NICK).encode())
    s.send("USER {} {} bla :{}\r\n".format(IDENT, HOST, REALNAME).encode())
    s.send("JOIN :{}\r\n".format(CHAN).encode())
    return s

class message:
    def __init__(self, text, to):
        self.recipient = to
        self.text = text
        self.sent = False

def mesg(msg):
    """
    Send message, return number of bytes sent
    """
    print("hi")
    return s.send("PRIVMSG {} :{}\r\n".format(msg.recipient, msg.text).encode())

def trans(line, sendto, lang):
    """
    Translate message
    """
    totrans = ""
    translation = ""
    for x in line[3:]:
        totrans = totrans + (x + " ")
    totrans = totrans[1:]
    blob = TextBlob(totrans)
    try:				# for error if same language
        translation = blob.translate(to=lang)
    except Exception as e:
        print("THREAD An exception of type {0} occurred. Arguments:\n{1!r}".format(type(e).__name__, e.args))
        return
    if(sendto == USER):
        #mesg(line[0], to)
        translation = line[0] + ": " + str(translation)
    msgqueue.append(message(str(translation), sendto))
    print("THREAD Translation: {}".format(translation))

#s = create_conn()

def listen():
    readbuffer = ""
    while True:					# loop FOREVER (exit with ctrl c)
        # all of the code between set 1 and set 2 is just putting the message received from the server into a nice format for us
        # set 1
        readbuffer=readbuffer+s.recv(1024).decode()		# store info sent from the server into
        print("LTHREAD received data")
        temp=readbuffer.split("\n")		# remove \n from the readbuffer and store in a temp variable
        readbuffer=temp.pop( )			# restore readbuffer to empty
        #totranslate = ""

        for line in temp:				# parse through every line read from server
	        # turn line into a list
            line=line.rstrip()
            line=line.split()

            # set 2
            if(line[0]=="PING"):			#if irc server sends a ping, pong back at it
                PONG = True
                print("LTHREAD PONG")
            elif(line[2]==CHAN):	#if a message comes in from the channel
                print("LTHREAD message sent from " + CHAN)
                thread = Thread(target = trans, args = (line, USER, userlang))
                thread.handled = False
                thread.start()
                threads.append(thread)
    	        #line[0] is user ident

            elif(line[0][1:len(USER)+1] == USER and line[2]==NICK): #if user privmsg us
                #transmesg(line, CHAN, chanlang)
                thread = Thread(target = trans, args = (line, CHAN, chanlang))
                thread.handled = False
                thread.start()
                threads.append(thread)

if __name__ == '__main__':
    s = create_conn()

    listenthread = Thread(target = listen)
    listenthread.start()

    while(True):
        if PONG:
            s.send("PONG {}\r\n".format(line[1]).encode())
            print("MAIN PONG")
            PONG = False

        # clean up thread pool
        for t in threads:
            if not t.isAlive():
                t.handled = True
            else:
                t.handled = False

        threads = [t for t in threads if not t.handled]

        # lol, it's all fancy and multithreaded now but this approach is probably more inherently error prone
        # whatever, it's just an experimental project anyway
        for m in msgqueue:
            print("in queue for")
            mesg(m)
            m.sent = True

        # if socket sent 0 bytes we retry
        msgqueue = [m for m in msgqueue if not m.sent]

        if len(threads) > 0:
            print("MAIN Threads: {}".format(len(threads)))
        #print(totranslate)

        if len(msgqueue) != 0:
            print("MAIN WARNING - Message queue not empty - {} items".format(len(msgqueue)))
