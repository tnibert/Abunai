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
readbuffer=""					#variable to read in what the server sends us
threads = []

def create_conn():
    # open connection to irc server
    s=socket.socket( )
    s.connect((HOST, PORT))
    s.send("NICK {}\r\n".format(NICK).encode())
    s.send("USER {} {} bla :{}\r\n".format(IDENT, HOST, REALNAME).encode())
    s.send("JOIN :{}\r\n".format(CHAN).encode())
    return s

def mesg(text, to):
	s.send("PRIVMSG {} :{}\r\n".format(to, text).encode())

def transmesg(line, sendto, lang):
    """
    Translate and send message
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
    mesg(str(translation), sendto)
    print("THREAD Translation: {}".format(translation))

s = create_conn()

while True:					# loop FOREVER (exit with ctrl c)
    # all of the code between set 1 and set 2 is just putting the message received from the server into a nice format for us
    # set 1
    readbuffer=readbuffer+s.recv(1024).decode()		# store info sent from the server into
    print("MAIN received data")
    temp=readbuffer.split("\n")		# remove \n from the readbuffer and store in a temp variable
    readbuffer=temp.pop( )			# restore readbuffer to empty
    #totranslate = ""

    for line in temp:				# parse through every line read from server
	    # turn line into a list
        line=line.rstrip()
        line=line.split()

        # set 2
        if(line[0]=="PING"):			#if irc server sends a ping, pong back at it
            s.send("PONG {}\r\n".format(line[1]).encode())
            print("MAIN PONG")
        elif(line[2]==CHAN):	#if a message comes in from the channel
            print("MAIN message sent from " + CHAN)
            thread = Thread(target = transmesg, args = (line, USER, userlang))
            thread.start()
            threads.append(thread)
    	    #line[0] is user ident

        elif(line[0][1:len(USER)+1] == USER and line[2]==NICK): #if user privmsg us
            #transmesg(line, CHAN, chanlang)
            thread = Thread(target = transmesg, args = (line, CHAN, chanlang))
            thread.start()
            threads.append(thread)

        # clean up thread pool
        for t in threads:
            if not t.isAlive():
                t.handled = True
            else:
                t.handled = False

        threads = [t for t in threads if not t.handled]

        print("MAIN Threads: {}".format(len(threads)))
        #print(totranslate)

        print("MAIN temp: %s" % temp)
        #print("readbuffer: %s" % readbuffer)

