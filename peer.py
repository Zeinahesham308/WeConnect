'''
    ##  Implementation of peer
    ##  Each peer has a client and a server side that runs on different threads
    ##  150114822 - Eren Ulaş
'''
import json
import re
import socket
from socket import *
import threading
import time
import select
import logging
import GUI
from colorama import Fore, Style, init
from pyfiglet import Figlet

# Create a Figlet object
fig = Figlet(font='slant', width=100)

clients = {}

##############################ADDED##################################
bold_pattern = r'\*\*(?=[^\s\*])(.*?)([^\s\*])\*\*'
italic_pattern = r'(?<!\S)_(?=\S)(.*?)(?<=\S)_(?!\S)'


# Server side of peer
class PeerServer(threading.Thread):

    # Peer server initialization
    def __init__(self, username, peerServerPort):
        threading.Thread.__init__(self)
        # keeps the username of the peer
        self.username = username
        # tcp socket for peer server
        self.tcpServerSocket = socket(AF_INET, SOCK_STREAM)
        # port number of the peer server
        self.peerServerPort = peerServerPort
        # if 1, then user is already chatting with someone
        # if 0, then user is not chatting with anyone
        self.isChatRequested = 0
        # keeps the socket for the peer that is connected to this peer
        self.connectedPeerSocket = None
        # keeps the ip of the peer that is connected to this peer's server
        self.connectedPeerIP = None
        # keeps the port number of the peer that is connected to this peer's server
        self.connectedPeerPort = None
        self.udpServerSocket=socket(AF_INET, SOCK_DGRAM)
        # online status of the peer
        self.isOnline = True
        # keeps the username of the peer that this peer is chatting with
        self.chattingClientName = None

        ######Added ##### Dictionary to store clients for each chat room
        self.chat_rooms = {}
        self.roomflag=None


        # main method of the peer server thread
    def run(self):
        if self.roomflag ==None:
            GUI.print_colored("Peer server started...You are now ONLINE", Fore.LIGHTGREEN_EX, Style.BRIGHT)    #this appears after the peer is logged in
            print()
            # gets the ip address of this peer
            # first checks to get it for Windows devices
            # if the device that runs this application is not windows
            # it checks to get it for macOS devices
            hostname=gethostname()
            try:
                self.peerServerHostname=gethostbyname(hostname)
            except gaierror:
                import netifaces as ni
                self.peerServerHostname = ni.ifaddresses('en0')[ni.AF_INET][0]['addr']

            # ip address of this peer
            #self.peerServerHostname = 'localhost'

            # socket initializations for the server of the peer
            self.tcpServerSocket.bind((self.peerServerHostname, self.peerServerPort))
            self.tcpServerSocket.listen(4)

            # inputs sockets that should be listened
            inputs = [self.tcpServerSocket]

            # server listens as long as there is a socket to listen in the inputs list and the user is online
            while inputs and self.isOnline:
                # monitors for the incoming connections
                try:
                    readable, writable, exceptional = select.select(inputs, [], [])
                    # If a server waits to be connected enters here
                    for s in readable:
                        # if the socket that is receiving the connection is the tcp socket of the peer's server, enters here
                        if s is self.tcpServerSocket and self.roomflag==None:
                            # accepts the connection, and adds its connection socket to the inputs  so that we can monitor that socket as well
                            connected, addr = s.accept()
                            connected.setblocking(0)
                            inputs.append(connected)
                            # if the user is not chatting, then the ip and the socket of this peer is assigned to server variables

                            if self.isChatRequested == 0 :
                                print(self.username + " is connected from " + str(addr))
                                self.connectedPeerSocket = connected
                                self.connectedPeerIP = addr[0]
                        # if the socket that receives the data is the one that
                        # is used to communicate with a connected peer, then enters here

                        else:
                            # message is received from connected peer
                            messageReceived = s.recv(1024).decode()
                            # logs the received message
                            logging.info("Received from " + str(self.connectedPeerIP) + " -> " + str(messageReceived))

                            # if message is a request message it means that this is the receiver side peer server
                            # so evaluate the chat request
                            if len(messageReceived) > 11 and messageReceived[:12] == "CHAT-REQUEST":
                                # text for proper input choices is printed however OK or REJECT is taken as input in main process of the peer
                                # if the socket that we received the data belongs to the peer that we are chatting with,
                                # enters here
                                if s is self.connectedPeerSocket:
                                    # parses the message
                                    messageReceived = messageReceived.split()
                                    # gets the port of the peer that sends the chat request message
                                    self.connectedPeerPort = int(messageReceived[1])
                                    # gets the username of the peer sends the chat request message
                                    self.chattingClientName = messageReceived[2]
                                    # prints prompt for the incoming chat request
                                    GUI.print_colored(f"Incoming chat request from {self.chattingClientName} >>",
                                                      Fore.LIGHTBLUE_EX, Style.BRIGHT)
                                    print()
                                    GUI.print_colored("Enter ", Fore.LIGHTBLACK_EX, Style.BRIGHT)
                                    GUI.print_colored("OK", Fore.LIGHTGREEN_EX, Style.BRIGHT)
                                    GUI.print_colored(" to accept or", Fore.LIGHTBLACK_EX, Style.BRIGHT)
                                    GUI.print_colored(" REJECT", Fore.LIGHTRED_EX, Style.BRIGHT)
                                    GUI.print_colored(" to reject:  ", Fore.LIGHTBLACK_EX, Style.BRIGHT)
                                    print()
                                    # makes isChatRequested = 1 which means that peer is chatting with someone
                                    self.isChatRequested = 1

                                # if the socket that we received the data does not belong to the peer that we are chatting with
                                # and if the user is already chatting with someone else(isChatRequested = 1), then enters here
                                elif s is not self.connectedPeerSocket and self.isChatRequested == 1:
                                    # sends a busy message to the peer that sends a chat request when this peer is
                                    # already chatting with someone else
                                    message = "BUSY"
                                    s.send(message.encode())
                                    # remove the peer from the inputs list so that it will not monitor this socket
                                    inputs.remove(s)

                            # if an OK message is received then ischatrequested is made 1 and then next messages will be shown to the peer of this server
                            elif messageReceived == "OK":
                                self.isChatRequested = 1

                            # if an REJECT message is received then ischatrequested is made 0 so that it can receive any other chat requests
                            elif messageReceived == "REJECT":
                                self.isChatRequested = 0
                                inputs.remove(s)

                            # if a message is received, and if this is not a quit message ':q' and
                            # if it is not an empty message, show this message to the user
                            elif messageReceived[:2] != ":q" and len(messageReceived) != 0:
                                print(self.chattingClientName + ": " + messageReceived)
                            # if the message received is a quit message ':q',
                            # makes ischatrequested 1 to receive new incoming request messages
                            # removes the socket of the connected peer from the inputs list
                            elif messageReceived[:2] == ":q":
                                self.isChatRequested = 0
                                inputs.clear()
                                inputs.append(self.tcpServerSocket)
                                # connected peer ended the chat
                                if len(messageReceived) == 2:
                                    print("User you're chatting with ended the chat")
                                    print("Press enter to quit the chat: ")
                            # if the message is an empty one, then it means that the
                            # connected user suddenly ended the chat(an error occurred)
                            elif len(messageReceived) == 0:
                                self.isChatRequested = 0
                                inputs.clear()
                                inputs.append(self.tcpServerSocket)
                                print("User you're chatting with suddenly ended the chat")
                                print("Press enter to quit the chat: ")

                # handles the exceptions, and logs them
                except OSError as oErr:
                    logging.error("OSError: {0}".format(oErr))
                except ValueError as vErr:
                    logging.error("ValueError: {0}".format(vErr))
        else :
            pass


######################
# Client side of peer

class PeerClient(threading.Thread):
    # variable initializations for the client side of the peer

    def __init__(self, ipToConnect, portToConnect, username, peerServer, responseReceived,roomflag,chatroom_name,registryIP,roomport):
        threading.Thread.__init__(self)
        # keeps the ip address of the peer that this will connect
        self.ipToConnect = ipToConnect
        # keeps the username of the peer
        self.username = username
        # keeps the port number that this client should connect
        self.portToConnect = portToConnect
        # keeps the server of this client
        self.peerServer = peerServer
        # keeps the phrase that is used when creating the client
        # if the client is created with a phrase, it means this one received the request
        # this phrase should be none if this is the client of the requester peer
        self.responseReceived = responseReceived

        # keeps if this client is ending the chat or not
        self.isEndingChat = False


        self.roomflag = roomflag
        self.chatroomname = chatroom_name
        self.joinedroomflag =None
        self.tcpClientSocket = socket(AF_INET, SOCK_STREAM)
        self.udpClientSocket=socket(AF_INET, SOCK_DGRAM)
        self.tcpClientServerSocket=socket(AF_INET, SOCK_STREAM)
        self.registryPort = 15600
        self.registryIP=registryIP
        self.roomport=roomport

    # main method of the peer client thread
    def run(self):

        if self.roomflag == None :
            print("Peer client started...")
            # connects to the server of other peer
            self.tcpClientSocket.connect((self.ipToConnect, self.portToConnect))

            # if the server of this peer is not connected by someone else and if this is the requester side peer client then enters here
            if self.peerServer.isChatRequested == 0 and self.responseReceived is None:

                # composes a request message and this is sent to server and then this waits a response message from the server this client connects
                requestMessage = "CHAT-REQUEST " + str(self.peerServer.peerServerPort)+ " " + self.username

                # logs the chat request sent to other peer
                logging.info("Send to " + self.ipToConnect + ":" + str(self.portToConnect) + " -> " + requestMessage)
                # sends the chat request
                self.tcpClientSocket.send(requestMessage.encode())
                print("Request message " + requestMessage + " is sent...")


                # received a response from the peer which the request message is sent to
                self.responseReceived = self.tcpClientSocket.recv(1024).decode()
                # logs the received message
                logging.info("Received from " + self.ipToConnect + ":" + str(self.portToConnect) + " -> " + self.responseReceived)
                print("Response is " + self.responseReceived)
                # parses the response for the chat request
                self.responseReceived = self.responseReceived.split()


                ###############################Updated####################################################

                # if response is ok then incoming messages will be evaluated as client messages and will be sent to the connected server
                if self.responseReceived[0] == "OK":
                    GUI.print_colored("Enter :q to leave the chat\n", Fore.LIGHTYELLOW_EX, Style.BRIGHT)
                    GUI.print_colored("Write Bold message in this form (**text**).... Write Italic message in this form (_text_) \n", Fore.LIGHTYELLOW_EX, Style.BRIGHT)
                    # changes the status of this client's server to chatting
                    self.peerServer.isChatRequested = 1
                    # sets the server variable with the username of the peer that this one is chatting

                    self.peerServer.chattingClientName = self.responseReceived[1]

                    # as long as the server status is chatting, this client can send messages
                    while self.peerServer.isChatRequested == 1:
                        # message input prompt
                        messageSent = input("")

                        messageSent = self.send_message_bold(messageSent)

                        messageSent = self.send_message_Italic(messageSent)

                        # sends the message to the connected peer, and logs it
                        self.tcpClientSocket.send(messageSent.encode())
                        logging.info("Send to " + self.ipToConnect + ":" + str(self.portToConnect) + " -> " + messageSent)
                        # if the quit message is sent, then the server status is changed to not chatting
                        # and this is the side that is ending the chat
                    #   self.handle_chat_room_messages(messageSent) ###########ADDED ##############
                        if messageSent == ":q":
                            self.peerServer.isChatRequested = 0
                            self.isEndingChat = True
                            break

                    # if peer is not chatting, checks if this is not the ending side
                    if self.peerServer.isChatRequested == 0:
                        if not self.isEndingChat:
                            # tries to send a quit message to the connected peer
                            # logs the message and handles the exception
                            try:
                                self.tcpClientSocket.send(":q ending-side".encode())
                                logging.info("Send to " + self.ipToConnect + ":" + str(self.portToConnect) + " -> :q")

                            except BrokenPipeError as bpErr:
                                logging.error("BrokenPipeError: {0}".format(bpErr))
                        # closes the socket
                        self.responseReceived = None
                        self.tcpClientSocket.close()

                # if the request is rejected, then changes the server status, sends a reject message to the connected peer's server
                # logs the message and then the socket is closed
                elif self.responseReceived[0] == "REJECT":
                    self.peerServer.isChatRequested = 0
                    print("client of requester is closing...")
                    self.tcpClientSocket.send("REJECT".encode())
                    logging.info("Send to " + self.ipToConnect + ":" + str(self.portToConnect) + " -> REJECT")
                    self.tcpClientSocket.close()
                # if a busy response is received, closes the socket
                elif self.responseReceived[0] == "BUSY":
                    print("Receiver peer is busy")
                    self.tcpClientSocket.close()



            # if the client is created with OK message it means that this is the client of receiver side peer
            #So it sends an OK message to the requesting side peer server that it connects and then waits for the user inputs.

        ###############################Updated####################################################
            elif self.responseReceived == "OK":
                # server status is changed
                self.peerServer.isChatRequested = 1
                # ok response is sent to the requester side
                okMessage = "OK"
                self.tcpClientSocket.send(okMessage.encode())
                logging.info("Send to " + self.ipToConnect + ":" + str(self.portToConnect) + " -> " + okMessage)
                print("Client with OK message is created... and sending messages")
                GUI.print_colored( "Enter :q to leave the chat\n", Fore.LIGHTYELLOW_EX, Style.BRIGHT)
                GUI.print_colored( "Write Bold message in this form (**text**)..... Write Italic message in this form (_text_) \n", Fore.LIGHTYELLOW_EX, Style.BRIGHT)

                # client can send messsages as long as the server status is chatting
                while self.peerServer.isChatRequested == 1:
                    # input prompt for user to enter message
                    messageSent = input("")

                    messageSent = self.send_message_bold(messageSent)

                    messageSent = self.send_message_Italic(messageSent)

                    self.tcpClientSocket.send(messageSent.encode())
                    logging.info("Send to " + self.ipToConnect + ":" + str(self.portToConnect) + " -> " + messageSent)
                    # if a quit message is sent, server status is changed
                    if messageSent == ":q":
                        self.peerServer.isChatRequested = 0
                        self.isEndingChat = True
                        break
                # if server is not chatting, and if this is not the ending side
                # sends a quitting message to the server of the other peer
                # then closes the socket
                if self.peerServer.isChatRequested == 0:
                    if not self.isEndingChat:
                        self.tcpClientSocket.send(":q ending-side".encode())
                        logging.info("Send to " + self.ipToConnect + ":" + str(self.portToConnect) + " -> :q")
                    self.responseReceived = None
                    self.tcpClientSocket.close()
        else :
            self.peerServer.roomflag =1

    #####################ADDED##############################
    def send_message_bold(self, message):
        # Use re.sub to replace bold matches with formatted text
        formatted_message = re.sub(bold_pattern, r"\033[1m\1\033[0m\2", message)
        return formatted_message

    def send_message_Italic(self, message):
        formatted_message = re.sub(italic_pattern, r"\033[3m\1\033[0m", message)
        return formatted_message



###########################################Updated#######################################
class PeerChatRoom(threading.Thread):
    def __init__(self, ipToConnect, portToConnect, username, peerServer, responseReceived,roomflag,chatroom_name,registryIP,roomport):
        threading.Thread.__init__(self)
        # keeps the ip address of the peer that this will connect
        self.ipToConnect = ipToConnect
        # keeps the username of the peer
        self.username = username
        # keeps the port number that this client should connect
        self.portToConnect = portToConnect
        # keeps the server of this client
        self.peerServer = peerServer
        # keeps the phrase that is used when creating the client
        # if the client is created with a phrase, it means this one received the request
        # this phrase should be none if this is the client of the requester peer
        self.responseReceived = responseReceived

        # keeps if this client is ending the chat or not
        self.isEndingChat = False

        self.chatroomname = chatroom_name
        self.joinedroomflag =None
        self.tcpClientSocket = socket(AF_INET, SOCK_STREAM)
        self.udpClientSocket=socket(AF_INET, SOCK_DGRAM)
        self.tcpClientServerSocket=socket(AF_INET, SOCK_STREAM)
        self.registryPort = 15600
        self.registryIP=registryIP
        self.roomport=roomport

    def run(self):
        if self.joinedroomflag is None:
            try:
                # Ensure self.ipToConnect and self.registryPort are valid
                ip_address = str(self.registryIP)
                port = int(self.registryPort)

                # Connect to the server
                self.tcpClientServerSocket.connect((ip_address, port))

                # Send the JOIN-ROOM request
                request_message = f"JOIN-ROOM {self.chatroomname} {self.username} "
                self.tcpClientServerSocket.send(request_message.encode())

                # Receive the response
                self.responseReceived = self.tcpClientServerSocket.recv(1024).decode()

                #                  self.tcpClientServerSocket.close()
                # Set the flag
                self.joinedroomflag = 1
            except Exception as e:
                print(f"Error connecting to server: {e}")

        messages = self.responseReceived
        message = messages.split(" ", 1)
        print(message[0])

        if message[0] == "JOIN-ROOM-SUCCESS":
            # self.tcpClientSocket.connect((str(self.registryIP), self.roomport))
            # self.tcpClientSocket.listen(4)
            # self.tcpClientSocket, addr = self.tcpClientSocket.accept()
            # self.registryIP=addr[0]
            # self.portToConnect=addr[1]

            GUI.print_colored(f"You joined {self.chatroomname} successfully... Enter QUIT to exit chatroom \n", Fore.LIGHTYELLOW_EX, Style.BRIGHT)
            GUI.print_colored("Write Bold message in this form (**text**).... Write Italic message in this form (_text_) \n", Fore.LIGHTYELLOW_EX, Style.BRIGHT)

            self.udpClientSocket.bind((self.registryIP, int(self.roomport)))
            join_message = f"{self.username} joined the chat !"
            # self.udpClientSocket.sendto(join_message.encode(), (self.registryIP,int( self.roomport)))
            self.broadcast_message(self.chatroomname, join_message, self.username)
            receive_thread = threading.Thread(target=self.receive, args=(self.username, self.chatroomname))
            receive_thread.start()
            time.sleep(0.1)

            # Assuming self.loginCredentials[0] and room_name are available in this context
            send_thread = threading.Thread(target=self.write, args=(self.username, self.chatroomname))
            send_thread.start()
            receive_thread.join()
            send_thread.join()

            #########################################################
            # self.tcpClientSocket = socket(AF_INET, SOCK_STREAM)
            # self.tcpClientSocket.connect((self.registryName, self.registryPort))
            # self.tcpClientSocket.connect((self.ipToConnect, self.portToConnect))

        elif message[0] == "JOIN-ROOM-FAIL":
            GUI.print_colored("NO ROOM WITH THIS NAME TRY JOINING AGAIN \n", Fore.LIGHTRED_EX, Style.BRIGHT)
            self.roomflag = None
            self.tcpClientSocket.close()

        else:
            print("IAM HEREEEEEE")
        # elif message[0] =="LEAVE-ROOM":
        #     requestMessage = f"LEAVE-ROOM {self.chatroomname} {self.username} "
        #     self.tcpClientServerSocket.send(requestMessage.encode())

    def broadcast_message(self, chatroom_name, message, sender_username):
        try:
            # self.tcpClientServerSocket = socket(AF_INET, SOCK_STREAM)
            # self.tcpClientServerSocket.connect((self.registryIP,self.registryPort))
            request_message = f"RETRIEVE_PORTS {chatroom_name}"
            self.tcpClientServerSocket.send(request_message.encode())
            response = self.tcpClientServerSocket.recv(1024).decode()
            #
            # self.tcpClientServerSocket.close()
            # Process the response
            if response.startswith("PEER_PORTS"):
                peer_ports = list(map(int, response.split()[1:]))
                if not peer_ports:
                    logging.warning(f"No peers found in chat room: {chatroom_name}")
                    return

                for room_port in peer_ports:
                    try:
                        # Use self.udpClientSocket for broadcasting
                        broadcast_message = sender_username + "->" + message
                        logging.info(f"Send to {room_port} -> {broadcast_message}")
                        self.udpClientSocket.sendto(broadcast_message.encode(), (self.registryIP, room_port))
                    except Exception as e:
                        logging.error(f"Error broadcasting message to peer on port {room_port}: {str(e)}")
                else:
                    logging.warning(f"Unable to retrieve ports from the registry: {response}")
        except Exception as e:
            logging.error(f"Error connecting to registry: {str(e)}")

    def receive(self, peername, chatroom_name):
        while True:
            try:
                message, sender_address = self.udpClientSocket.recvfrom(1024)
                message = message.decode()

                if message.startswith("PEERNAME"):
                    response_message = f"{peername}: {message.split()[1]}"
                    self.udpClientSocket.sendto(response_message.encode(), sender_address)
                else:
                    print(message)

            except Exception as e:
                print(f"Error in receive loop: {str(e)}")
                self.roomflag = None
                self.peerServer.roomflag = None
                self.udpClientSocket.close()
                self.tcpClientSocket.close()
                self.tcpClientServerSocket.close()
                self.udpClientSocket.close()
                break

    def write(self, peername, room_name=None):
        time.sleep(1)
        while True:
            try:
                content = input("")
                if content == "QUIT":
                    leave_message = f"{peername} left the chat!!!"
                    self.broadcast_message(room_name, leave_message, peername)
                    message = f"LEAVE-ROOM {peername} {room_name}"
                    self.tcpClientServerSocket.send(message.encode())
                    response = self.tcpClientServerSocket.recv(1024).decode()
                    time.sleep(1)
                    if response.startswith("LEAVE-ROOM-SUCCESS"):
                        message = f"REMOVE-PORT-ROOM {peername} {room_name}"
                        self.tcpClientServerSocket.send(message.encode())
                        # response = self.tcpClientServerSocket.recv(1024).decode()
                        self.roomflag = None
                        self.joinedroomflag = None
                        # self.tcpClientSocket.close()
                        # self.tcpClientServerSocket.close()
                        self.udpClientSocket.close()
                        break
                    else:
                        print("Something went wrong, and you haven't left the chat")
                else:
                    # message = f"Enter- {peername} {room_name} {content}"
                    message = f"{content}"
                    message = self.send_message_bold(message)

                    message = self.send_message_Italic(message)

                    # Use broadcast_message function instead of UDP socket
                    self.broadcast_message(room_name, message, peername)
            except Exception as e:
                print(f"Error in write loop: {str(e)}")
                break

    def send_message_bold(self, message):
        # Use re.sub to replace bold matches with formatted text
        formatted_message = re.sub(bold_pattern, r"\033[1m\1\033[0m\2", message)
        return formatted_message

    def send_message_Italic(self, message):
        formatted_message = re.sub(italic_pattern, r"\033[3m\1\033[0m", message)
        return formatted_message


###############ADDED##############################

class peerMain:

    # peer initializations
    def __init__(self):
        # ip address of the registry
        self.registryName = input("Enter IP address of registry: ")
        # port number of the registry
        self.registryPort = 15600
        # tcp socket connection to registry
        self.tcpClientSocket = socket(AF_INET, SOCK_STREAM)

        self.tcpClientSocket.connect((self.registryName,self.registryPort))

        # initializes udp socket which is used to send hello messages
        self.udpClientSocket = socket(AF_INET, SOCK_DGRAM)

        # udp port of the registry
        self.registryUDPPort = 15500
        # login info of the peer
        self.loginCredentials = (None, None)
        # online status of the peer
        self.isOnline = False
        # server port number of this peer
        self.peerServerPort = None
        # server of this peer
        self.peerServer = None
        # client of this peer
        self.peerClient = None
        # Peer Chat Room
        self.PeerChatRoom = None
        # timer initialization
        self.timer = None
        self.stop_threads = False
        self.room_name=None

        choice = "0"
        entered = "0" ###############
        # log file initialization
        logging.basicConfig(filename="peer.log", level=logging.INFO)
        # as long as the user is not logged out, asks to select an option in the menu
        ascii_art = fig.renderText("W.e.l.c.o.m.e to !!")
        print(ascii_art)
        ascii_art = fig.renderText("WE CONNECT CHAT ")
        print(ascii_art)

        while entered == "0":###################

            choice = input("Choose: \nCreate account: 1\nLogin: 2\n")
            if choice == "1":
                username = input("username: ")
                GUI.print_colored("Password should be of at least 8 characters must including (special char , Lowercase, uppercase,numbers)",Fore.YELLOW, Style.BRIGHT)
                print()

                password = input("password: ")
                self.createAccount(username, password)

            elif choice == "2" and not self.isOnline:
                username = input("username: ")
                password = input("password: ")
                # asks for the port number for server's tcp socket
                peerServerPort = int(input("Enter a port number for peer server: "))
                status = self.login(username, password, peerServerPort)
                if status == 1:
                    self.isOnline = True
                    self.loginCredentials = (username, password)
                    self.peerServerPort = peerServerPort
                    # creates the server thread for this peer, and runs it
                    self.peerServer = PeerServer(self.loginCredentials[0], self.peerServerPort)
                    self.peerServer.start()
                    # hello message is sent to registry
                    self.sendHelloMessage()
                    entered=1

        while choice != "8":
            # menu selection prompt
            choice = input("WELCOME .... \nChoose:\nList online users: 1\nlist availabe group chat rooms: 2\nStart a chat with a user: 3\nSearch a user: 4\nSearch a group chat room: 5\ncreate a group chat room: 6\nJoin a group chat room: 7\nLogout: 8\n")

            if choice == "1":
                self.retrievepeers()

            elif choice == "2" :
                self.list_chat_rooms()

            elif choice == "3":
                username = input("Enter the username of user to start chat: ")
                searchStatus = self.searchUser(username)
                # if searched user is found, then its ip address and port number is retrieved
                # and a client thread is created
                # main process waits for the client thread to finish its chat
                if searchStatus != None and searchStatus != 0:
                    searchStatus = searchStatus.split(":")
                    self.peerClient = PeerClient(searchStatus[0], int(searchStatus[1]) , self.loginCredentials[0], self.peerServer, None,None,None,None,None)
                    self.peerClient.start()
                    self.peerClient.join()

            elif choice == "4" :
                username = input("Username to be searched: ")
                searchStatus = self.searchUser(username)
                # if user is found its ip address is shown to user
                if searchStatus != None and searchStatus != 0:
                    print("IP address of " + username + " is " + searchStatus)

            elif choice == "5":
                # User wants to search for a group chat room
                room_name = input("Enter the name of the chat room to search: ")
                room_status = self.search_room_status(room_name)
                if room_status is not None:
                    # Handle the room status as needed
                    GUI.print_colored(f"It's port number: {room_status} ", Fore.LIGHTBLUE_EX, Style.BRIGHT)
                    print()

            elif choice == "6" and self.isOnline:
                self.create_chat_room()

            ##############################ADDED##################################
            elif choice == "7" and self.isOnline:
                room_name = input("Enter the chat room name to join: ")
                self.room_name=room_name
                room_Port = input("Enter the chat room port: ")
                room_status = self.search_room_status(room_name)

                # Now you can use room_status as needed in your program
                if room_status:
                    # Notify that the peer joined the chat
                    #self.join_chat_room(room_name, self.loginCredentials[0])
                    # Implement your logic for chatting within the room, e.g., starting a new thread
                    # to handle receiving and sending messages within the chat room.
                    #GUI.print_colored( "Enter QUIT to exit chatroom \n", Fore.LIGHTYELLOW_EX, Style.BRIGHT)
                    # Example of starting a thread for receiving messages
                    # Assuming self.loginCredentials[0] contains the peer's name
                    self.add_room_port(room_Port)
                    self.PeerChatRoom = PeerChatRoom(self.registryPort, self.peerServerPort , self.loginCredentials[0], self.peerServer, None, 1,self.room_name,self.registryName,room_Port)
                    self.PeerChatRoom.start()
                    self.PeerChatRoom.join()
                    # self.tcpClientSocket = socket(AF_INET, SOCK_STREAM)
                    #
                    # self.tcpClientSocket.connect((self.registryName, self.registryPort))

                    # Now, the peer is actively participating in the chat room.
                else:
                    print(f"The chat room '{room_name}' does not exist.")

            elif choice == "8":
                self.logout(1)
                self.logout(2)
                self.isOnline = False
                self.loginCredentials = (None, None)
                self.peerServer.isOnline = False
                self.peerServer.tcpServerSocket.close()
                if self.peerClient is not None:
                    self.peerClient.tcpClientSocket.close()
                print("Logged out successfully")
            # is peer is not logged in and exits the program
            # if choice is 4 and user is online, then user is asked
            # for a username that is wanted to be searched

            # if choice is 3 and user is online, then user is asked
            # to enter the username of the user that is wanted to be chatted


            # if this is the receiver side then it will get the prompt to accept an incoming request during the main loop
            # that's why response is evaluated in main process not the server thread even though the prompt is printed by server
            # if the response is ok then a client is created for this peer with the OK message and that's why it will directly
            # sent an OK message to the requesting side peer server and waits for the user input
            # main process waits for the client thread to finish its chat
            elif choice == "OK" and self.isOnline:
                okMessage = "OK " + self.loginCredentials[0]
                logging.info("Send to " + self.peerServer.connectedPeerIP + " -> " + okMessage)
                self.peerServer.connectedPeerSocket.send(okMessage.encode())
                self.PeerClient = PeerClient(self.peerServer.connectedPeerIP, self.peerServer.connectedPeerPort , self.loginCredentials[0], self.peerServer, "OK",None,None,None,None)
                self.PeerClient.start()
                self.PeerClient.join()
            # if user rejects the chat request then reject message is sent to the requester side
            elif choice == "REJECT" and self.isOnline:
                self.peerServer.connectedPeerSocket.send("REJECT".encode())
                self.peerServer.isChatRequested = 0
                logging.info("Send to " + self.peerServer.connectedPeerIP + " -> REJECT")
            # if choice is cancel timer for hello message is cancelled
            elif choice == "CANCEL":
                self.timer.cancel()
                break

        # if main process is not ended with cancel selection
        # socket of the client is closed
        if choice != "CANCEL":
            self.tcpClientSocket.close()



    # account creation function
    def createAccount(self, username, password):
        # join message to create an account is composed and sent to registry
        # if response is success then informs the user for account creation
        # if response is exist then informs the user for account existence
        message = "JOIN " + username + " " + password
        logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)
        self.tcpClientSocket.send(message.encode())
        response = self.tcpClientSocket.recv(1024).decode()
        logging.info("Received from " + self.registryName + " -> " + response)
        if response == "join-success":
            print("Account created...")
        elif response == "NotValid-Password":
            print("Password does not meet the criteria. Signup again or login")
        elif response == "join-exist":
            print("choose another username or login...")

    # login function
    def login(self, username, password, peerServerPort):
        # a login message is composed and sent to registry
        # an integer is returned according to each response
        message = "LOGIN " + username + " " + password + " " + str(peerServerPort)
        logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)
        self.tcpClientSocket.send(message.encode())
        response = self.tcpClientSocket.recv(1024).decode()
        logging.info("Received from " + self.registryName + " -> " + response)
        if response == "login-success":

            GUI.print_colored("Logged in successfully...", Fore.LIGHTGREEN_EX, Style.BRIGHT)
            print()
            return 1
        elif response == "login-account-not-exist":
            GUI.print_colored("Account does not exist...", Fore.LIGHTRED_EX, Style.BRIGHT)
            print()
            return 0
        elif response == "login-online":
            GUI.print_colored("Account is already online...", Fore.LIGHTYELLOW_EX, Style.BRIGHT)
            print()
            return 2
        elif response == "login-wrong-password":
            GUI.print_colored("Wrong password...", Fore.LIGHTRED_EX, Style.BRIGHT)
            print()
            return 3

    # logout function
    def logout(self, option):
        # a logout message is composed and sent to registry
        # timer is stopped
        if option == 1:
            message = "LOGOUT " + self.loginCredentials[0]
            self.timer.cancel()
        else:
            message = "LOGOUT"
        logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)
        self.tcpClientSocket.send(message.encode())

#################added#####################################
    def retrievepeers(self):
        message = "LIST-PEERS"
        logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)

        self.tcpClientSocket.send(message.encode())

        response = self.tcpClientSocket.recv(1024).decode()

        logging.info("Received from " + self.registryName + " -> " + response)
        # Process the response to extract the list of peers

        if response.startswith("Online-Peers: "):
            online_peers = response.split(": ")[1].split(", ")
            #print("Online Peers:", online_peers)
            GUI.print_colored("Online Peers:", Fore.LIGHTGREEN_EX, Style.BRIGHT)
            GUI.print_colored(f"{online_peers}\n", Fore.LIGHTGREEN_EX, Style.BRIGHT)
        else:
            print(response)  # Print the message indicating no online


    #####################################ADDED######################
    def list_chat_rooms(self):
        message = "LIST-GROUPS"
        logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)

        self.tcpClientSocket.send(message.encode())

        response = self.tcpClientSocket.recv(1024).decode()

        logging.info("Received from " + self.registryName + " -> " + response)

        # Process the response to extract the list of peers
        if response.startswith("LIST-GROUPS-SUCCESS"):
            try:

                online_groups = response.split(": ")[1].split(", ")
                GUI.print_colored("Available Chat Rooms: ", Fore.LIGHTGREEN_EX, Style.BRIGHT)
                GUI.print_colored(f"{online_groups}\n", Fore.LIGHTGREEN_EX, Style.BRIGHT)
            except IndexError:
                print(response)
                print("Error parsing the response. The format may be incorrect.")
        else:
            print(response)  # Print the message indicating no online

    def create_chat_room(self):
        room_name = input("Enter the chat room name: ")
        room_port = input("Enter the chat room port: ")  # Add this line to get the port from the user

        message = f"CREATE-CHAT-ROOM {room_name} {self.loginCredentials[0]} {room_port}"
        logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)
        self.tcpClientSocket.send(message.encode())
        response = self.tcpClientSocket.recv(1024).decode()

        logging.info("Received from " + self.registryName + " -> " + response)
        print(response)

    def search_room_status(self, room_name):
        # a search message for the chat room is composed and sent to the database
        message = "SEARCH_ROOM " + room_name
        logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)
        self.tcpClientSocket.send(message.encode())
        response = self.tcpClientSocket.recv(1024).decode().split()
        logging.info("Received from " + self.registryName + " -> " )

        if response[0] == "search-room-success":
            GUI.print_colored(f"{room_name} is found successfully...", Fore.LIGHTGREEN_EX, Style.BRIGHT)
            print()
            return response[1]
        elif response[0] == "search-room-not-found":
            GUI.print_colored(f"{room_name} is not found\n", Fore.LIGHTRED_EX, Style.BRIGHT)
            print()
            return None

    def add_room_port(self, room_port):
        try:
            # Prepare the message to send to the registry
            message = f"ADD-PORT {room_port} {self.loginCredentials[0]}"

            # Send the message to the registry
            self.tcpClientSocket.send(message.encode())

            # Receive the response if needed
            response = self.tcpClientSocket.recv(1024).decode()
            print(response)
            # Handle the response as per your requirements

        except Exception as e:
            print(f"Error in add_room_port: {str(e)}")

    def searchUser(self, username):
        # a search message is composed and sent to registry
        # custom value is returned according to each response
        # to this search message
        message = "SEARCH " + username
        logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)
        self.tcpClientSocket.send(message.encode())
        response = self.tcpClientSocket.recv(1024).decode().split()
        logging.info("Received from " + self.registryName + " -> " + " ".join(response))
        if response[0] == "search-success":
            GUI.print_colored(f" {username} is found successfully...", Fore.LIGHTGREEN_EX, Style.BRIGHT)
            print()
            return response[1]
        elif response[0] == "search-user-not-online":
            GUI.print_colored(f" {username}  is not online...", Fore.LIGHTRED_EX, Style.BRIGHT)
            print()
            return 0
        elif response[0] == "search-user-not-found":
            GUI.print_colored(f" {username}   is not found", Fore.LIGHTRED_EX, Style.BRIGHT)
            print()

            return None

    # function for sending hello message
    # a timer thread is used to send hello messages to udp socket of registry
    def sendHelloMessage(self):
        message = "HELLO " + self.loginCredentials[0]
        logging.info("Send to " + self.registryName + ":" + str(self.registryUDPPort) + " -> " + message)
        self.udpClientSocket.sendto(message.encode(), ((self.registryName), self.registryUDPPort))
        self.timer = threading.Timer(1, self.sendHelloMessage)
        self.timer.start()

# peer is started
main = peerMain()