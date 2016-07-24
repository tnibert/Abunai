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
#import goslate
#import os
#import urllib, urllib2, re

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
	print "invalid args"
	print "Usage: python abunai.py SERVER NICK CHANNEL USERNICK USERLANGUAGE CHANNELLANGUAGE"
	print "do not include the # in the channel name"
	exit()

#if you want to manually set the info...
#HOST=""
#PORT=6667
#NICK="Bot"
#IDENT="Bot"
#REALNAME="Bot"
#CHAN="#abu"
readbuffer=""					#variable to read in what the server sends us

#set up translator
#gs = goslate.Goslate()

#open connection to irc server
s=socket.socket( )
s.connect((HOST, PORT))
s.send("NICK %s\r\n" % NICK)
s.send("USER %s %s bla :%s\r\n" % (IDENT, HOST, REALNAME))
s.send("JOIN :%s\r\n" % CHAN)
#s.send("PRIVMSG %s :%s\r\n" % (CHAN, "PHj33R!"))
#s.send("PRIVMSG %s :%s\r\n" % (CHAN, "I am a bot"))

def mesg(text, to):
	s.send("PRIVMSG %s :%s\r\n" % (to, text))

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
		print "same language"
	if(sendto == USER):
		print "test"
		#mesg(line[0], to)
		print line[0]
		print translation
		print type(translation)
		translation = line[0] + ": " + str(translation)
	mesg(str(translation), sendto)
	print translation
	#except:
	#	print "same language"

while 1:					#loop FOREVER
    #all of the code between set 1 and set 2 is just putting the message received from the server into a nice format for us
    #set 1
    readbuffer=readbuffer+s.recv(1024)		#store info sent from the server into
    temp=string.split(readbuffer, "\n")		#remove \n from the readbuffer and store in a temp variable
    readbuffer=temp.pop( )			#restore readbuffer to empty
    totranslate = ""

    for line in temp:				#parse through every line read from server
	#turn line into a list
	line=string.rstrip(line)
        line=string.split(line)

	#set 2
        if(line[0]=="PING"):			#if irc server sends a ping, pong back at it
            s.send("PONG %s\r\n" % line[1])
	elif(line[2]==CHAN):	#if a message comes in from the channel
	    print "message sent from " + CHAN
	    transmesg(line, USER, userlang)
		#line[0] is user ident

	elif(line[0][1:len(USER)+1] == USER and line[2]==NICK): #if user privmsg us
	    #mesg(line[3:]
	    transmesg(line, CHAN, chanlang)
	    #mesg(gs.translate(totranslate, 'de'))
	    #translate the text
	#mesg(line[0][1:len(USER)])
	#this is an example of how you might go about parsing input
	#this is the place where that type of thing happens
	#elif(line[len(line)-1]==":pheer"):		#if the last element is :pheer, aka if a user enters pheer in irc 
    	#	s.send("PRIVMSG %s :%s\r\n" % (CHAN, "1337 skillz"))		#respond with "1337 skillz"
	#	mesg("this is a test", CHAN)

	#mesg(line[0][1:len(USER)])

	#:
	#	if(word == CHAN):
	#		totranslate = totranslate + word
	#	elif(len(totranslate) > 0):
	#		totranslate = totranslate + word + " "
	print(totranslate)
	#print(gs.translate(totranslate, 'de'))

	#debug output
        #print "line: %s" % line
	#print "lend: %d" % len(line)
	print "temp: %s" % temp
	print "readbuffer: %s" % readbuffer


#begin open web page
#hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
#       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
#       'Accept-Encoding': 'none',
#       'Accept-Language': 'en-US,en;q=0.8',
#       'Connection': 'keep-alive'}
#url = "https://translate.google.com/#es/en/Mi%20nombre%20es%20Tim"
#req = urllib2.Request(url, headers=hdr)
#try:
#    page = urllib2.urlopen(req)
#except urllib2.HTTPError, e:
#    print e.fp.read()
#soup = BeautifulSoup(page, "lxml")
#page.close()
