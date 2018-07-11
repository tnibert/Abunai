#! /usr/bin/env python
#Abunai v2.0
#an irc translation bot script
#released by Timothy Nibert, 29 May 2016
#call with python abunai.py server nick channel USER USERLANGUAGE CHANNELLANGUAGE
#do not include the # sign in the channel arg
import sys
import socket
import string
from textblob import TextBlob

#declare variables for where bot goes
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

#if you want to manually set the info...
#HOST=""
#PORT=6667
#NICK="Bot"
#IDENT="Bot"
#REALNAME="Bot"
#CHAN="#abu"
readbuffer=""					#variable to read in what the server sends us

#open connection to irc server
s=socket.socket( )
s.connect((HOST, PORT))
s.send("NICK {}\r\n".format(NICK).encode())
s.send("USER {} {} bla :{}\r\n".format(IDENT, HOST, REALNAME).encode())
s.send("JOIN :{}\r\n".format(CHAN).encode())

def mesg(text, to):
	s.send("PRIVMSG {} :{}\r\n".format(to, text).encode())

def transmesg(line, sendto, lang):
	totrans = ""
	translation = ""
	for x in line[3:]:
		totrans = totrans + (x + " ")
	totrans = totrans[1:]
	blob = TextBlob(totrans)
	try:				#for error if same language
		translation = blob.translate(to=lang)
	except:
		print("same language")
	if(sendto == USER):
		print("test")
		#mesg(line[0], to)
		print(line[0])
		print(translation)
		print(type(translation))
		translation = line[0] + ": " + str(translation)
	mesg(str(translation), sendto)
	print(translation)
	#except:
	#	print "same language"

while 1:					#loop FOREVER
    #all of the code between set 1 and set 2 is just putting the message received from the server into a nice format for us
    #set 1
    readbuffer=readbuffer+s.recv(1024).decode()		#store info sent from the server into
    temp=readbuffer.split("\n")		#remove \n from the readbuffer and store in a temp variable
    readbuffer=temp.pop( )			#restore readbuffer to empty
    totranslate = ""

    for line in temp:				#parse through every line read from server
	#turn line into a list
        line=line.rstrip()
        line=line.split()

        #set 2
        if(line[0]=="PING"):			#if irc server sends a ping, pong back at it
            s.send("PONG {}\r\n".format(line[1]).encode())
        elif(line[2]==CHAN):	#if a message comes in from the channel
            print("message sent from " + CHAN)
            transmesg(line, USER, userlang)
    	    #line[0] is user ident

        elif(line[0][1:len(USER)+1] == USER and line[2]==NICK): #if user privmsg us
            transmesg(line, CHAN, chanlang)
        print(totranslate)
        #print(gs.translate(totranslate, 'de'))

        #debug output
            #print "line: %s" % line
        #print "lend: %d" % len(line)
        print("temp: %s" % temp)
        print("readbuffer: %s" % readbuffer)

