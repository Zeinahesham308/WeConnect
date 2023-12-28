'''
    ##  Implementation of peer
    ##  Each peer has a client and a server side that runs on different threads
    ##  150114822 - Eren Ulaş
'''
import json
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


        # online status of the peer
        self.isOnline = True

        # keeps the username of the peer that this peer is chatting with
        self.chattingClientName = None

        ######Added ##### Dictionary to store clients for each chat room
        self.chat_rooms = {}
        self.roomflag=None

        # main method of the peer server thread
    def run(self):

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
                    if s is self.tcpServerSocket:
                        # accepts the connection, and adds its connection socket to the inputs  so that we can monitor that socket as well
                        connected, addr = s.accept()
                        connected.setblocking(0)
                        inputs.append(connected)
                        # if the user is not chatting, then the ip and the socket of this peer is assigned to server variables
                        if self.isChatRequested == 0 and self.roomflag==0:
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


                        #########   Added ############################
                        # elif messageReceived.startswith("JOIN_CHAT_ROOM"):
                        #     self.handle_chat_room_messages(messageReceived[len("JOIN_CHAT_ROOM"):].strip())
                        # elif messageReceived.startswith("LEAVE_CHAT_ROOM"):
                        #     self.handle_chat_room_messages(messageReceived[len("LEAVE_CHAT_ROOM"):].strip())
                        # elif messageReceived.startswith("CHAT_ROOM_MESSAGE"):
                        #     self.handle_chat_room_messages(messageReceived[len("CHAT_ROOM_MESSAGE"):].strip())
                        # ######################
            # handles the exceptions, and logs them
            except OSError as oErr:
                logging.error("OSError: {0}".format(oErr))
            except ValueError as vErr:
                logging.error("ValueError: {0}".format(vErr))

    #########   Added ############################


######################
# Client side of peer

class PeerClient(threading.Thread):
    # variable initializations for the client side of the peer
    def __init__(self, ipToConnect, portToConnect, username, peerServer, responseReceived,roomflag):
        threading.Thread.__init__(self)
        # keeps the ip address of the peer that this will connect
        self.ipToConnect = ipToConnect
        # keeps the username of the peer
        self.username = username
        # keeps the port number that this client should connect
        self.portToConnect = portToConnect
        # client side tcp socket initialization
        self.tcpClientSocket = socket(AF_INET, SOCK_STREAM)
        # keeps the server of this client
        self.peerServer = peerServer
        # keeps the phrase that is used when creating the client
        # if the client is created with a phrase, it means this one received the request
        # this phrase should be none if this is the client of the requester peer
        self.responseReceived = responseReceived
        # keeps if this client is ending the chat or not
        self.isEndingChat = False
        self.roomflag =roomflag

#
    # main method of the peer client thread
    def run(self):
        if self.peerServer.roomflag == None:
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



                # if response is ok then incoming messages will be evaluated as client messages and will be sent to the connected server
                if self.responseReceived[0] == "OK":

                    # changes the status of this client's server to chatting
                    self.peerServer.isChatRequested = 1
                    # sets the server variable with the username of the peer that this one is chatting

                    self.peerServer.chattingClientName = self.responseReceived[1]


                    # as long as the server status is chatting, this client can send messages
                    while self.peerServer.isChatRequested == 1:
                        # message input prompt
                        messageSent = input(self.username + ": ")
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


            elif self.responseReceived == "OK":
                # server status is changed
                self.peerServer.isChatRequested = 1
                # ok response is sent to the requester side
                okMessage = "OK"
                self.tcpClientSocket.send(okMessage.encode())
                logging.info("Send to " + self.ipToConnect + ":" + str(self.portToConnect) + " -> " + okMessage)
                print("Client with OK message is created... and sending messages")

                # client can send messsages as long as the server status is chatting
                while self.peerServer.isChatRequested == 1:
                    # input prompt for user to enter message
                    messageSent = input(self.username + ": ")
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
            print("chat room started...")
            while self.roomflag == 1:
                # input prompt for user to enter message
                messageSent = input(self.username + ": ")
                self.tcpClientSocket.send(messageSent.encode())
                logging.info("Send to " + self.ipToConnect + ":" + str(self.portToConnect) + " -> " + messageSent)
                # if a quit message is sent, server status is changed
                if messageSent == ":q":
                    self.peerServer.isChatRequested = 0
                    self.isEndingChat = True
                    break

###############ADDED##############################

class PeerServerGroup(threading.Thread):
    def __init__(self, ip, port, username, peerServer, action, chat_room):
        threading.Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.username = username
        self.peerServer = peerServer
        self.action = action
        self.chat_room = chat_room
        self.clients = {}  # Dictionary to store connected clients and their sockets
        self.serverSocket = socket(AF_INET, SOCK_STREAM)
        self.serverSocket.bind((ip, port))
        self.serverSocket.listen(5)

    def run(self):
        while True:
            connection, client_address = self.serverSocket.accept()
            threading.Thread(target=self.handle_group_connection, args=(connection,)).start()

    def handle_group_connection(self, connection):
        try:
            while True:
                data = connection.recv(1024).decode()
                if not data:
                    break
                message = json.loads(data)
                if message['action'] == 'JOIN':
                    self.handle_group_join(connection, message)
                elif message['action'] == 'MESSAGE':
                    self.handle_group_message(message)
        except Exception as e:
            logging.error(f"Error in group connection: {e}")
        finally:
            connection.close()

    def handle_group_join(self, connection, message):
        username = message['username']
        group = message.get('chat_room', None)
        if group == self.chat_room:
            self.clients[username] = connection
            logging.info(f"{username} joined the group {self.chat_room}.")
            self.broadcast_message(username, f"{username} joined the group {self.chat_room}.")
        else:
            logging.warning(f"{username} tried to join the wrong group ({group}).")

    def handle_group_message(self, message):
        sender = message['username']
        content = message['content']
        logging.info(f"Received message from {sender} in group {self.chat_room}: {content}")
        self.broadcast_message(sender, content)

    def broadcast_message(self, sender, content):
        for username, client_socket in self.clients.items():
            if username != sender:
                message = {'action': 'BROADCAST', 'sender': sender, 'content': content}
                client_socket.send(json.dumps(message).encode())

class PeerClientGroup(threading.Thread):
    def __init__(self, serverIP, serverPort, username, peerServer, action, chat_room):
        threading.Thread.__init__(self)
        self.serverIP = serverIP
        self.serverPort = serverPort
        self.username = username
        self.peerServer = peerServer
        self.action = action
        self.chat_room = chat_room
        self.clientSocket = socket(AF_INET, SOCK_STREAM)

    def run(self):
        try:
            self.clientSocket.connect((self.serverIP, self.serverPort))
            threading.Thread(target=self.receive_group_messages).start()
            self.join_group()
            self.send_group_messages()
        except Exception as e:
            logging.error(f"Error connecting to group server: {e}")

    def receive_group_messages(self):
        try:
            while True:
                data = self.clientSocket.recv(1024).decode()
                if not data:
                    break
                message = json.loads(data)
                if message['action'] == 'BROADCAST':
                    sender = message['sender']
                    content = message['content']
                    print(f"[{sender}]: {content}")
        except Exception as e:
            logging.error(f"Error receiving group messages: {e}")

    def join_group(self):
        message = {'action': 'JOIN', 'username': self.username, 'chat_room': self.chat_room}
        self.clientSocket.send(json.dumps(message).encode())

    def send_group_messages(self):
        try:
            while True:
                content = input("Enter message: ")
                message = {'action': 'MESSAGE', 'username': self.username, 'content': content}
                self.clientSocket.send(json.dumps(message).encode())
        except Exception as e:
            logging.error(f"Error sending group messages: {e}")
class peerMain:

    # peer initializations
    def __init__(self):
        # ip address of the registry
        self.peerClientGroup = None
        self.PeerServerGroup =None
        self.registryName = input("Enter IP address of registry: ")
        #self.registryName = 'localhost'
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
        # timer initialization
        self.timer = None
        
        choice = "0"
        entered = "0" ###############
        # log file initialization
        logging.basicConfig(filename="peer.log", level=logging.INFO)
        # as long as the user is not logged out, asks to select an option in the menu
        ascii_art = fig.renderText("W.e.l.c.o.m.e to !!")
        print(ascii_art)
        ascii_art = fig.renderText("WE CONNECT CHAT ")
        print(ascii_art)

        while entered=="0":###################

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

            # if choice is 1, creates an account with the username
            # and password entered by the user

            # if choice is 3 and user is logged in, then user is logged out
            # and peer variables are set, and server and client sockets are closed
            if choice == "1":
                self.retrievepeers()
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
            elif choice == "4" :
                username = input("Username to be searched: ")
                searchStatus = self.searchUser(username)
                # if user is found its ip address is shown to user
                if searchStatus != None and searchStatus != 0:
                    print("IP address of " + username + " is " + searchStatus)
            # if choice is 5 and user is online, then user is asked
            # to enter the username of the user that is wanted to be chatted
            elif choice == "3":
                username = input("Enter the username of user to start chat: ")
                searchStatus = self.searchUser(username)
                # if searched user is found, then its ip address and port number is retrieved
                # and a client thread is created
                # main process waits for the client thread to finish its chat
                if searchStatus != None and searchStatus != 0:
                    searchStatus = searchStatus.split(":")
                    self.peerClient = PeerClient(searchStatus[0], int(searchStatus[1]) , self.loginCredentials[0], self.peerServer, None,None)
                    self.peerClient.start()
                    self.peerClient.join()
         ##############################ADDED##################################
            elif choice == "2" :
                self.list_chat_rooms()
            elif choice == "6" and self.isOnline:
                self.create_chat_room()
            elif choice == "7" and self.isOnline:
                room_name = input("Enter the chat room name to join: ")
                #room_Port = input("Enter the chat room port: ")
                room_status = self.search_room_status(room_name)

                # Now you can use room_status as needed in your program
                if room_status:
                    # Notify that the peer joined the chat
                    self.join_chat_room(room_name, self.loginCredentials[0])

                    # Implement your logic for chatting within the room, e.g., starting a new thread
                    # to handle receiving and sending messages within the chat room.

                    # Example of starting a thread for receiving messages
                    receive_thread = threading.Thread(target=self.receive)
                    receive_thread.start()

                    # Example of starting a thread for sending messages
                    send_thread = threading.Thread(target=self.write(self.loginCredentials[0],room_name))
                    send_thread.start()

                    receive_thread.join()
                    send_thread.join()

                    # Now, the peer is actively participating in the chat room.

                else:
                    print(f"The chat room '{room_name}' does not exist.")



                # peer_server_group = PeerServerGroup(str(self.registryName), int(room_Port),
                #                                     self.loginCredentials[0], self.peerServer, 'JOIN',room_name)
                # peer_server_group.start()
                # self.join_chat_room(room_name)

             ##############################ADDED##################################
            # if this is the receiver side then it will get the prompt to accept an incoming request during the main loop
            # that's why response is evaluated in main process not the server thread even though the prompt is printed by server
            # if the response is ok then a client is created for this peer with the OK message and that's why it will directly
            # sent an OK message to the requesting side peer server and waits for the user input
            # main process waits for the client thread to finish its chat
            elif choice == "OK" and self.isOnline:
                okMessage = "OK " + self.loginCredentials[0]
                logging.info("Send to " + self.peerServer.connectedPeerIP + " -> " + okMessage)
                self.peerServer.connectedPeerSocket.send(okMessage.encode())
                self.peerClient = PeerClient(self.peerServer.connectedPeerIP, self.peerServer.connectedPeerPort , self.loginCredentials[0], self.peerServer, "OK")
                self.peerClient.start()
                self.peerClient.join()
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
        ##############################ADDED##################################
            # elif choice == "2":
            #     self.retrievegroups()
            #
            # elif choice =="6":
            #     #create a group chat room
            #     GUI.print_colored("Enter the chat room name : ", Fore.LIGHTCYAN_EX,Style.BRIGHT)
            #     chatroom_name= input()
            #     self.createChatRoom(chatroom_name)
            ##############################ADDED##################################


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

    #def retrievegroups(self): #lesaaaaaaaaa

    # def createChatRoom(self,chatroom_name):
    #     # Send a request to the server to create a chat room
    #     request_message = f"CREATE-CHAT-ROOM {chatroom_name}"
    #     self.tcpClientSocket.send(request_message.encode())
    #     logging.info(f"Send to {self.registryName}:{self.registryPort} -> {request_message}")
    #
    #     # Receive the response from the server
    #     response_message = self.tcpClientSocket.recv(1024).decode()
    #     logging.info(f"Received from {self.registryName}:{self.registryPort} -> {response_message}")
    #
    #     # Parse the response
    #     response_parts = response_message.split()
    #     if response_parts[0] == "create-chat-room-success":
    #         print(f"Chat room '{chatroom_name}' created successfully!")
    #
    #         # Now, you can join the chat room
    #         self.joinChatRoom(chatroom_name)
    #
    #     elif response_parts[0] == "create-chat-room-fail":
    #         print(f"Failed to create chat room '{chatroom_name}'. Reason: {response_parts[1]}")
    #     else:
    #         print(f"Unexpected response from the server: {response_message}")
    # def joinChatRoom(self, chatroom_name):
    #     # Assuming you have a list of active chat rooms in your peerMain class
    #     # This list can be used to keep track of the chat rooms the peer has joined
    #     # You might want to extend this logic based on your specific implementation
    #
    #     #if chatroom_name not in self.activeChatRooms:
    #         # Create a PeerClient for the chat room
    #     chatroom_client = PeerClient(self.loginCredentials[0], self.peerServerPort, self.registryName,self.registryPort,None)
    #     chatroom_client.join_chat_room(chatroom_name)
    #     chatroom_client.start()
    #         # Add the chat room to the list of active chat rooms
    #         #self.activeChatRooms.append(chatroom_name)
    #     #else:
    #         #print(f"You are already in the chat room '{chatroom_name}'.")

    ######################################
    # def join_chat_room(self,room_name):
    #
    #     self.peerClientGroup = PeerClientGroup(self.registryName, self.registryPort, self.loginCredentials[0],
    #                                            self.peerServer, "JOIN_CHAT_ROOM",room_name)
    #     self.peerClientGroup.start()
    #     self.peerClientGroup.join()


    #####################################ADDED#######################
    def create_chat_room(self):
        room_name = input("Enter the chat room name: ")
        room_port = input("Enter the chat room port: ")  # Add this line to get the port from the user

        message = f"CREATE-CHAT-ROOM {room_name} {self.loginCredentials[0]} {room_port}"
        logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)
        self.tcpClientSocket.send(message.encode())
        response = self.tcpClientSocket.recv(1024).decode()

        logging.info("Received from " + self.registryName + " -> " + response)
        print(response)

    # def join_chat_room(self):
    #     room_name = input("Enter the chat room name to join: ")
    #     message = f"JOIN_CHAT_ROOM {room_name} {self.loginCredentials[0]}"
    #     self.tcpClientSocket.send(message.encode())

    def list_chat_rooms(self):
        message = "LIST-GROUPS"
        logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)

        self.tcpClientSocket.send(message.encode())

        response = self.tcpClientSocket.recv(1024).decode()

        logging.info("Received from " + self.registryName + " -> " + response)

        # Process the response to extract the list of peers
        if response.startswith("LIST-GROUPS-SUCCESS"):
            try:

                online_groups = response.split(" ")[1:]
                GUI.print_colored("Available Chat Rooms: ", Fore.LIGHTGREEN_EX, Style.BRIGHT)
                GUI.print_colored(f"{online_groups}\n", Fore.LIGHTGREEN_EX, Style.BRIGHT)
            except IndexError:
                print(response)
                print("Error parsing the response. The format may be incorrect.")
        else:
            print(response)  # Print the message indicating no online

    def search_room_status(self, room_name):
        # a search message for the chat room is composed and sent to the database
        message = "SEARCH_ROOM " + room_name
        logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)
        self.tcpClientSocket.send(message.encode())
        response = self.tcpClientSocket.recv(1024).decode().split()
        logging.info("Received from " + self.registryName + " -> " )

        if response[0] == "search-room-success":
            GUI.print_colored(f" {room_name} is found successfully...", Fore.LIGHTGREEN_EX, Style.BRIGHT)
            print()
            return response[1]
        elif response[0] == "search-room-not-found":
            GUI.print_colored(f" {room_name} is not found", Fore.LIGHTRED_EX, Style.BRIGHT)
            print()
            return None

    # In your peer class
    def receive(self):
        while True:
            try:
                message = self.tcpClientSocket.recv(1024).decode()
                if not message:
                    break
                print(message)
            except Exception as e:
                print("Error receiving message:", e)
                break

    def write(self,peername,room_name):
        while True:

                message = f"Enter-message/{peername}:{input('')} {room_name}"
                self.tcpClientSocket.send(message.encode())

    # Function to join a chat room
    def join_chat_room(self, chatroom_name,Peername):
        message = f"JOIN-ROOM {chatroom_name} {Peername}"
        self.tcpClientSocket.send(message.encode())


    # Function to leave a chat room
    def leave_chat_room(self, chatroom_name,Peername):
        message = f"LEAVE-ROOM {chatroom_name} {Peername}"
        self.tcpClientSocket.send(message.encode())
    #####################################ADDED#######################
    # function for searching an online user
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
        self.udpClientSocket.sendto(message.encode(), (self.registryName, self.registryUDPPort))
        self.timer = threading.Timer(1, self.sendHelloMessage)
        self.timer.start()

# peer is started
main = peerMain()