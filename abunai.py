#! /usr/bin/env python
# Abunai v2.2
# IRC translator bot
# call with python abunai.py server nick channel USER USERLANGUAGE CHANNELLANGUAGE
# do not include the # sign in the channel arg
# as is, this script won't play nicely with servers that need nickserv
import sys
import socket
from queue import Queue
from threading import Thread
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

todo: is socket s unacceptable shared state?
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
END = "quit"

inmsgqueue = Queue()
outmsgqueue = Queue()
# when we connect to a network, it will probably forward us to a node
# indivserver is the node address preceeded with a : for ping pong
indivserver = ""
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
            # tell user who the message came from
            out_text = self.userident + ": " + str(out_text)
        mesg(self.recipient, out_text)


def mesg(recipient, text):
    """
    Send message, return number of bytes sent
    """
    return s.send("PRIVMSG {} :{}\r\n".format(recipient, text).encode())


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
        cur_msg.translate()
        outmsgqueue.put(cur_msg)


def send_thread():
    while not stopped:
        cur_msg = outmsgqueue.get()
        if cur_msg == END:
            print("Closing out send thread")
            continue

        print("Sending")
        try:
            cur_msg.send()
        # make catch more specific
        except Exception as e:
            outmsgqueue.put(cur_msg)
            continue


def listen():
    readbuffer = ""
    while not stopped:
        # all of the code between set 1 and set 2 is just putting the message received
        # from the server into a nice format for us to work with
        # todo: reexamine this munging, limiting our recv amount...
        # set 1
        readbuffer = readbuffer + s.recv(1024).decode()  # store info sent from the server
        print("LTHREAD received data")
        temp = readbuffer.split("\n")  # remove \n from the readbuffer and store in a temp variable
        readbuffer = temp.pop()  # restore readbuffer to empty

        for line in temp:  # parse through every line read from server
            print(line)
            # turn line into a list
            line = line.rstrip()
            line = line.split()

            # set 2
            if line[0] == "PING":  # if irc server sends a ping, pong back at it
                # this assignment (indivserver) really should only be done once
                indivserver = line[1]
                s.send("PONG {}\r\n".format(indivserver).encode())
                print("LTHREAD PONG")

            # if a message comes in from the channel, private message to our user
            elif line[2] == CHAN:
                print("LTHREAD message sent from " + CHAN)
                inmsgqueue.put(message(line, USER, userlang))

            # if user privmsg us, send to channel
            elif line[0][1:len(USER) + 1] == USER and line[2] == NICK:
                inmsgqueue.put(message(line, CHAN, chanlang))


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
    # todo: this will not finish until the socket is fed
    listenthread.join()

    print("Complete")
