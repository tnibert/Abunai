#! /usr/bin/env python
# Abunai v2.1
# an irc translation bot script
# call with python abunai.py server nick channel USER USERLANGUAGE CHANNELLANGUAGE
# do not include the # sign in the channel arg
# this script won't play nicely with servers that need nickserv as is
import sys
import socket
from queue import Queue
from threading import Thread
from textblob import TextBlob

"""
Threading:
We have three types of threads and two queues
- main thread (main program execution) - reads from queues, cleans queues, sends all messages
- listen thread - listens to socket, launches an appropriate translation thread, or if we get a ping sets pong flag true
- translation threads - launched by listen thread, does translation, appends the translated message to the msgqueue
We have one main thread and one listen thread, but we can have many translation threads going at one time.

threads variable is the thread queue, main thread checks if each thread is finished and removes them if they are
msgqueue variable is the message queue (outgoing messages), main thread checks msgqueue, sends messages, and removes them from the msgqueue
"""

# declare variables for where bot goes
try:
    HOST = sys.argv[1]
    PORT = 6667
    NICK = sys.argv[2]
    IDENT = sys.argv[2]
    REALNAME = sys.argv[2]
    CHAN = "#" + sys.argv[3]
    USER = sys.argv[4]
    userlang = sys.argv[5]
    chanlang = sys.argv[6]
except:
    print("invalid args")
    print("Usage: python abunai.py SERVER NICK CHANNEL USERNICK USERLANGUAGE CHANNELLANGUAGE")
    print("do not include the # in the channel name")
    exit()

# if you want to manually set the info...
# HOST=""
# PORT=6667
# NICK="Bot"
# IDENT="Bot"
# REALNAME="Bot"
# CHAN="#abu"

DEBUG = False

inmsgqueue = Queue()
outmsgqueue = Queue()
# when we connect to a network, it will probably forward us to a node
# indivserver is the node address preceeded with a : for ping pong
indivserver = ""


def create_conn():
    # open connection to irc server
    s = socket.socket()
    s.connect((HOST, PORT))
    s.send("NICK {}\r\n".format(NICK).encode())
    s.send("USER {} {} bla :{}\r\n".format(IDENT, HOST, REALNAME).encode())
    s.send("JOIN :{}\r\n".format(CHAN).encode())
    return s


class message:
    def __init__(self, line, to, lang):
        # line[0] is user ident
        self.userident = line[0]
        self.recipient = to
        self.text = extract_text_from_line(line)
        self.target_lang = lang
        self.sent = False

    def translate(self):
        blob = TextBlob(self.text)
        try:  # for error if same language
            self.text = blob.translate(to=self.target_lang)
        except Exception as e:
            print("THREAD An exception of type {0} occurred. Arguments:\n{1!r}".format(type(e).__name__, e.args))
            return

    def send(self):
        out_text = self.text
        if self.recipient == USER:
            out_text = self.userident + ": " + str(out_text)
        mesg(self)


def mesg(msg):
    """
    Send message, return number of bytes sent
    """
    return s.send("PRIVMSG {} :{}\r\n".format(msg.recipient, msg.text).encode())


def extract_text_from_line(line):
    """
    extract translateable text from the irc message
    :param line:
    :return:
    """
    totrans = ""
    for x in line[3:]:
        totrans = totrans + (x + " ")
    totrans = totrans[1:]
    return totrans


def translate_thread():
    while True:
        # Queue will block until item is available
        cur_msg = inmsgqueue.get()
        cur_msg.translate()
        outmsgqueue.put(cur_msg)


def send_thread():
    while True:
        cur_msg = outmsgqueue.get()
        try:
            cur_msg.send()
        # make catch more specific
        except Exception as e:
            outmsgqueue.put(cur_msg)
            continue


def listen():
    readbuffer = ""
    while True:  # loop FOREVER (exit with ctrl c)
        # all of the code between set 1 and set 2 is just putting the message received from the server into a nice format for us
        # set 1
        readbuffer = readbuffer + s.recv(1024).decode()  # store info sent from the server into
        print("LTHREAD received data")
        temp = readbuffer.split("\n")  # remove \n from the readbuffer and store in a temp variable
        readbuffer = temp.pop()  # restore readbuffer to empty
        # totranslate = ""

        for line in temp:  # parse through every line read from server
            # turn line into a list
            line = line.rstrip()
            line = line.split()

            # set 2
            if (line[0] == "PING"):  # if irc server sends a ping, pong back at it
                # this assignment (indivserver) really should only be done once
                indivserver = line[1]
                s.send("PONG {}\r\n".format(indivserver).encode())
                print("LTHREAD PONG")

            # if a message comes in from the channel, private message to our user
            elif (line[2] == CHAN):
                print("LTHREAD message sent from " + CHAN)
                inmsgqueue.put(message(line, USER, userlang))

            # if user privmsg us, send to channel
            elif (line[0][1:len(USER) + 1] == USER and line[2] == NICK):
                inmsgqueue.put(message(line, CHAN, chanlang))


if __name__ == '__main__':
    s = create_conn()

    listenthread = Thread(target=listen)
    translatethread = Thread(target=translate_thread)
    sendthread = Thread(target=send_thread)

    listenthread.start()
    translatethread.start()
    sendthread.start()

    listenthread.join()
    translatethread.join()
    send_thread().join()
