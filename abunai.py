#! /usr/bin/env python
# Abunai v2.2
# IRC translator bot
# call with python abunai.py server nick channel USER USERLANGUAGE CHANNELLANGUAGE
# do not include the # sign in the channel arg
# as is, this script won't play nicely with servers that need nickserv or sasl
# quit by entering q at the terminal

import sys
import socket
import traceback
from queue import Queue
from threading import Thread, Lock
from textblob import TextBlob

"""
Threading Architecture:
We have four threads and two queues

Threads:
- main thread (main program execution) - sets up everything, waits for user to input 'q' to quit
- listen thread - listens to socket, responds to PING, queues messages for translation
- translation thread - reads from queue, does translation, queues messages for sending
- send thread - reads from queue, sends message to server

Queues:
- inmsgqueue - bridges messages from listen thread to translation thread for translation
- outmsgqueue - bridges messages from translation thread to send thread for sending back to server

"""

# settings for bot from command invocation
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
# HOST="irc.whatever.net"
# PORT=6667
# NICK="Bot"
# IDENT="Bot"
# REALNAME="Bot"
# CHAN="#abu"
# USER="myusername"
# userlang = "en"
# chanlang = "es"

# this marker will be sent through the queues to stop the consumer threads
END = "quit"

inmsgqueue = Queue()
outmsgqueue = Queue()

# I don't think this lock is really necessary
# because I tested making simultaneous send() calls from
# multiple threads to netcat -l and nothing was garbled
# but always good to be safe
# We wrap our socket send() calls in this lock
socket_lock = Lock()

stopped = False


def create_conn():
    """
    Open connection to irc server
    :return: a socket
    """
    s = socket.socket()
    s.connect((HOST, PORT))
    s.send("NICK {}\r\n".format(NICK).encode())
    s.send("USER {} {} bla :{}\r\n".format(IDENT, HOST, REALNAME).encode())
    s.send("JOIN :{}\r\n".format(CHAN).encode())
    return s


class message:
    def __init__(self, line, to, lang):
        # line[0] is user ident
        self.userident = line[0].split("!")[0]
        self.recipient = to
        self.text = extract_text_from_line(line)
        self.target_lang = lang
        self.sent = False

    def translate(self):
        blob = TextBlob(self.text)
        self.text = blob.translate(to=self.target_lang)

    def send_info(self):
        out_text = self.text
        if self.recipient == USER:
            # tell user who the message came from
            out_text = self.userident + ": " + str(out_text)
        return self.recipient, out_text

    def __str__(self):
        return self.text


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
    while not stopped:
        # Queue will block until item is available
        cur_msg = inmsgqueue.get()
        if cur_msg == END:
            print("Closing out translate thread")
            continue

        print("Translating")
        try:
            cur_msg.translate()
        except Exception as e:
            print("Problem translating, sending untranslated: {}".format(cur_msg))
            traceback.print_exc()
        outmsgqueue.put(cur_msg)

    print("Translate thread complete")


def send_thread():
    while not stopped:
        cur_msg = outmsgqueue.get()
        if cur_msg == END:
            print("Closing out send thread")
            continue

        print("Sending")
        try:
            with socket_lock:
                s.send("PRIVMSG {} :{}\r\n".format(*cur_msg.send_info()).encode())
        # todo: make catch more specific
        except Exception as e:
            print("Problem sending message, retrying: {}".format(cur_msg))
            traceback.print_exc()
            outmsgqueue.put(cur_msg)
            continue

    print("Send thread complete")


def listen():
    while not stopped:
        # store buffer from the server
        readbuffer = s.recv(1024).decode()

        print("Listen thread received data")
        if len(readbuffer) == 0:
            continue

        # split the read buffer into separate lines
        temp = readbuffer.split("\n")
        # the last item is always empty or ":", discard
        temp.pop()

        # parse through every line read from server
        for line in temp:
            print(line)
            # turn line into a list
            line = line.rstrip()
            line = line.split()

            if len(line) < 2:
                continue

            if line[0] == "PING":  # if irc server sends a ping, pong back at it
                # indivserver is the node address in the irc network
                indivserver = line[1]
                with socket_lock:
                    s.send("PONG {}\r\n".format(indivserver).encode())
                print("PONG")
                continue

            if len(line) < 3:
                continue

            # if a message comes in from the channel, private message to our user
            if line[2] == CHAN:
                print("Message sent from " + CHAN)
                inmsgqueue.put(message(line, USER, userlang))

            # if user privmsg us, send to channel
            elif line[0][1:len(USER) + 1] == USER and line[2] == NICK:
                inmsgqueue.put(message(line, CHAN, chanlang))

    print("Listen thread complete")


if __name__ == '__main__':
    s = create_conn()
    print("Connection created")

    listenthread = Thread(target=listen)
    translatethread = Thread(target=translate_thread)
    sendthread = Thread(target=send_thread)

    listenthread.start()
    translatethread.start()
    sendthread.start()

    print("Threads started")

    # wait for quit signal
    while not stopped:
        c = sys.stdin.read(1)
        if c == 'q':
            print("Quit signal received")
            stopped = True
            with inmsgqueue.mutex:
                inmsgqueue.queue.clear()
            inmsgqueue.put(END)
            with outmsgqueue.mutex:
                outmsgqueue.queue.clear()
            outmsgqueue.put(END)

            s.shutdown(socket.SHUT_RDWR)

    print("Joining threads")
    sendthread.join()
    translatethread.join()
    listenthread.join()

    print("Complete")
