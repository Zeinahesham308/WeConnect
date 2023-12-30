'''
    ##  Implementation of registry
    ##  150114822 - Eren Ulaş
'''
import logging
import signal
import sys
import threading
from socket import *
import bcrypt
import select

import db




# This class is used to process the peer messages sent to registry
# for each peer connected to registry, a new client thread is created
class ClientThread(threading.Thread):
    # initializations for client thread
    def __init__(self, ip, port, tcpClientSocket):
        threading.Thread.__init__(self)
        # ip of the connected peer
        self.ip = ip
        # port number of the connected peer
        self.port = port
        # socket of the peer
        self.tcpClientSocket = tcpClientSocket
        # username, online status and udp server initializations
        self.username = None
        self.isOnline = True
        self.udpServer = None
        self.clients = {}
        print("New thread started for " + ip + ":" + str(port))

    # main of the thread
    def run(self):
        # locks for thread which will be used for thread synchronization
        self.lock = threading.Lock()
        print("Connection from: " + self.ip + ":" + str(port))
        print("IP Connected: " + self.ip)

        while True:
            try:
                # waits for incoming messages from peers
                message = self.tcpClientSocket.recv(1024).decode().split()
                logging.info("Received from " + self.ip + ":" + str(self.port) + " -> " + " ".join(message))
                #   JOIN    #

                if message[0] == "JOIN":
                    # join-exist is sent to peer,
                    # if an account with this username already exists
                    if db.is_account_exist(message[1]):
                        response = "join-exist"
                        print("From-> " + self.ip + ":" + str(self.port) + " " + response)
                        logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                        self.tcpClientSocket.send(response.encode())
                    # join-success is sent to peer,
                    # if an account with this username is not exist, and the account is created
                    else:
                        password = message[2]

                        # Check if the password meets the specified criteria
                        if (
                                len(password) >= 8 and
                                any(char.isdigit() for char in password) and  # At least one digit
                                any(char.islower() for char in password) and  # At least one lowercase letter
                                any(char.isupper() for char in password) and  # At least one uppercase letter
                                any(char in "!@#$%^&*()-_=+[]{}|;:'\",.<>/?`~" for char in password)
                                # At least one special character
                        ):
                            password = message[2]
                            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                            db.register(message[1], hashed)
                            response = "join-success"
                            logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                            self.tcpClientSocket.send(response.encode())
                        else:
                            response = "NotValid-Password"
                            print("From-> " + self.ip + ":" + str(self.port) + " " + response)
                            logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                            self.tcpClientSocket.send(response.encode())

                ############################################
                # LIST PEERS #
                elif message[0] == "LIST-PEERS":
                    online_peers = db.get_online_peers()
                    if online_peers:
                        response = "Online-Peers: "  + ', '.join(online_peers)
                    else:
                        response = "No online peers."
                    logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                    self.tcpClientSocket.send(response.encode())


                #elif message[0] == "LIST GROUPS":

                ###############ADDED###################################################################
                # LIST GROUPS #
                elif message[0] == "LIST-GROUPS":
                    chat_rooms = db.get_chat_rooms()
                    #print(response)
                    if chat_rooms:
                        response = "LIST-GROUPS-SUCCESS: " + ', '.join(chat_rooms)
                    else:
                        response = "No-available-rooms."
                    logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " )
                    self.tcpClientSocket.send(response.encode())


                elif message[0] == "SEARCH_ROOM":
                    # checks if a chat room with the given name exists
                    if db.is_chat_room_exist(message[1]):
                        response = "search-room-success " + str(db.get_room_port(message[1]))
                        logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                        self.tcpClientSocket.send(response.encode())
                    # enters if chat room does not exist
                    else:
                        response = "search-room-not-found"
                        logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                        self.tcpClientSocket.send(response.encode())

                elif message[0] == "RETRIEVE_PORTS":
                    chatroom_name = message[1]
                    # Retrieve ports for peers in the specified chat room
                    peer_ports = db.get_peer_room_ports_for_chatroom(chatroom_name)
                    if peer_ports:
                        response = "PEER_PORTS " + " ".join(map(str, peer_ports))
                    else:
                        response = "NO_PEERS_IN_CHATROOM"
                    self.tcpClientSocket.send(response.encode())


                elif message[0] == "ADD-PORT":
                    # Extract the room port and peer_username from the message
                    room_port = int(message[1])
                    peer_username = message[2]
                    # Handle the "ADD-PORT" message by adding the port to the database
                    db.online_peers_update_port(peer_username,room_port)
                    response="Room port added successfully to the peer"
                    self.tcpClientSocket.send(response.encode())
                    # Add more conditions to handle other types of messages if needed


                elif message[0] == "JOIN-ROOM":
                    chatroom_name = message[1]
                    peer_username = message[2]
                    # Check if the user is already in the chat room
                    if db.is_user_in_chat_room(peer_username, chatroom_name):
                        response = "JOIN-ROOM-FAIL User is already in the chat room"
                    else:
                        # logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                        db.add_user_to_chat_room(peer_username, chatroom_name)
                        self.clients[peer_username] = {'socket': self.tcpClientSocket, 'chatroom':chatroom_name}
                        response = "JOIN-ROOM-SUCCESS  " + ', '.join(self.clients)
                        self.tcpClientSocket.send(response.encode())


                    #self.broadcast_message(chatroom_name,f'{peer_username} joined the chat!',peer_username)
                    #self.tcpClientSocket.send("connected to the room server".encode())

                elif message[0]== "PEERNAME":
                    peer_username=message[2]
                    chatroom_name=message[1]
                    print(f"peer username is {peer_username}")
                    #self.broadcast_message(chatroom_name,f'{peer_username} joined the chat!',peer_username)
                    #self.tcpClientSocket.send("connected to the room server".encode())
                    #db.add_user_to_chat_room(peer_username, chatroom_name)

                elif message[0] == "LEAVE-ROOM":
                    peer_username = message[1]
                    chatroom_name=message[2]
                    db.remove_user_from_chat_room(peer_username, chatroom_name)
                    #self.broadcast_message(chatroom_name, f"{peer_username} left the chat", peer_username)
                    self.clients.pop(peer_username)
                    response = f"LEAVE-ROOM-SUCCESS {self.clients} "
                    self.tcpClientSocket.send(response.encode())
                    # Remove the peer from the chat room
                   #self.tcpClientSocket.close()

                elif message[0]=="REMOVE-PORT-ROOM":
                    peer_username = message[1]
                    chatroom_name = message[2]
                    db.remove_room_port(peer_username)
                    response = f"REMOVING-ROOM-PORT-SUCCESS {self.clients}"
                    self.tcpClientSocket.send(response.encode())

                # Handle CREATE-CHAT-ROOM command
                elif message[0] == "CREATE-CHAT-ROOM":
                    chatroom_name = message[1]
                    chatroom_port = message[3]  # Assuming the port is the third element in the message


                    if db.is_chat_room_exist(chatroom_name):
                        response = "CREATE-CHAT-ROOM-FAIL Chat room already exists."
                    else:
                        db.create_chat_room(chatroom_name, chatroom_port)
                        response = "CREATE-CHAT-ROOM-SUCCESS"

                    print(response)
                    logging.info(response)
                    self.tcpClientSocket.send(response.encode())

       #####################################################################################################
                #   LOGIN    #
                elif message[0] == "LOGIN":
                    # login-account-not-exist is sent to peer,
                    # if an account with the username does not exist

                    if not db.is_account_exist(message[1]):
                        response = "login-account-not-exist"
                        logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                        self.tcpClientSocket.send(response.encode())
                    # login-online is sent to peer,
                    # if an account with the username already online
                    elif db.is_account_online(message[1]):
                        response = "login-online"
                        logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                        self.tcpClientSocket.send(response.encode())
                    # login-success is sent to peer,
                    # if an account with the username exists and not online
                    else:
                        # retrieves the account's password, and checks if the one entered by the user is correct
                        retrievedPass = db.get_password(message[1])
                        # if password is correct, then peer's thread is added to threads list
                        # peer is added to db with its username, port number, and ip address
                        if bcrypt.checkpw(message[2].encode('utf-8'), retrievedPass):
                            self.username = message[1]
                            self.lock.acquire()
                            try:
                                tcpThreads[self.username] = self
                            finally:
                                self.lock.release()

                            db.user_login(message[1], self.ip, message[3])

                            #onlinePeers[message[1]] = newThread
                            # login-success is sent to peer,
                            # and a udp server thread is created for this peer, and thread is started
                            # timer thread of the udp server is started
                            response = "login-success"
                            logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                            self.tcpClientSocket.send(response.encode())
                            self.udpServer = UDPServer(self.username, self.tcpClientSocket)
                            self.udpServer.start()
                            self.udpServer.timer.start()
                        # if password not matches and then login-wrong-password response is sent
                        else:
                            response = "login-wrong-password"
                            logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                            self.tcpClientSocket.send(response.encode())
                #   LOGOUT  #
                elif message[0] == "LOGOUT":
                    # if user is online,
                    # removes the user from onlinePeers list
                    # and removes the thread for this user from tcpThreads
                    # socket is closed and timer thread of the udp for this
                    # user is cancelled

                    # if message[1] in onlinePeers:
                    #     del onlinePeers[message[1]]
                    if len(message) > 1 and message[1] is not None and db.is_account_online(message[1]):
                        db.user_logout(message[1])
                        self.lock.acquire()
                        try:
                            if message[1] in tcpThreads:
                                del tcpThreads[message[1]]
                        finally:
                            self.lock.release()
                        print(self.ip + ":" + str(self.port) + " is logged out")
                        self.tcpClientSocket.close()
                        self.udpServer.timer.cancel()
                        break
                    else:
                        self.tcpClientSocket.close()
                        break
                #   SEARCH  #
                elif message[0] == "SEARCH":
                    # checks if an account with the username exists
                    if db.is_account_exist(message[1]):
                        # checks if the account is online
                        # and sends the related response to peer
                        if db.is_account_online(message[1]):
                            peer_info = db.get_peer_ip_port(message[1])
                            response = "search-success " + peer_info[0] + ":" + peer_info[1]
                            logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                            self.tcpClientSocket.send(response.encode())
                        else:
                            response = "search-user-not-online"
                            logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                            self.tcpClientSocket.send(response.encode())
                    # enters if username does not exist
                    else:
                        response = "search-user-not-found"
                        logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                        self.tcpClientSocket.send(response.encode())
                # else:
                #
                #     self.broadcast_message(chatroom_name, content ,peer_username )

            except OSError as oErr:
                logging.error("OSError: {0}".format(oErr))


                # function for resettin the timeout for the udp timer thread

    def resetTimeout(self):
        self.udpServer.resetTimer()



class ClientManager:
    def _init_(self):
        self.clients = {}  # Dictionary to store peername-socket pairs

    def add_client(self, peername, socket):
        self.clients[peername] = socket

    def get_socket(self, peername):
        return self.clients.get(peername)

# Example usage:

# Create an instance of ClientManager


# Use desired_socket as needed


# implementation of the udp server thread for clients
class UDPServer(threading.Thread):

    # udp server thread initializations
    def __init__(self, username, clientSocket):
        threading.Thread.__init__(self)
        self.username = username
        # timer thread for the udp server is initialized
        self.timer = threading.Timer(3, self.waitHelloMessage)
        self.tcpClientSocket = clientSocket

    # if hello message is not received before timeout
    # then peer is disconnected
    def waitHelloMessage(self):
        if self.username is not None:
            db.user_logout(self.username)
            if self.username in tcpThreads:
                del tcpThreads[self.username]
        self.tcpClientSocket.close()
        print("Removed " + self.username + " from online peers")

    # resets the timer for udp server
    def resetTimer(self):
        self.timer.cancel()
        self.timer = threading.Timer(3, self.waitHelloMessage)
        self.timer.start()


# tcp and udp server port initializations
print("Registy started...")
port = 15600
portUDP = 15500

# db initialization
db = db.DB()

# gets the ip address of this peer
# first checks to get it for windows devices
# if the device that runs this application is not windows
# it checks to get it for macos devices
hostname = gethostname()
try:
    host = gethostbyname(hostname)
except gaierror:
    import netifaces as ni

    host = ni.ifaddresses('en0')[ni.AF_INET][0]['addr']

print("Registry IP address: " + host)
print("Registry port number: " + str(port))

# onlinePeers list for online account
onlinePeers = {}
# accounts list for accounts
accounts = {}
# tcpThreads list for online client's thread
tcpThreads = {}
nicknames=[]


# tcp and udp socket initializations
tcpSocket = socket(AF_INET, SOCK_STREAM)
udpSocket = socket(AF_INET, SOCK_DGRAM)
tcpSocket.bind((host, port))
udpSocket.bind((host, portUDP))
tcpSocket.listen(5)

# input sockets that are listened
inputs = [tcpSocket, udpSocket]

# log file initialization
logging.basicConfig(filename="registry.log", level=logging.INFO)
# Signal handler function

while inputs:

    print("Listening for incoming connections...")
    # monitors for the incoming connections
    readable, writable, exceptional = select.select(inputs, [], [])
    for s in readable:
        # if the message received comes to the tcp socket
        # the connection is accepted and a thread is created for it, and that thread is started
        if s is tcpSocket:
            tcpClientSocket, addr = tcpSocket.accept()
            #clients.append(tcpClientSocket) ###################################################
            newThread = ClientThread(addr[0], addr[1], tcpClientSocket)
            newThread.start()
        # if the message received comes to the udp socket
        elif s is udpSocket:
            # received the incoming udp message and parses it
            message, clientAddress = s.recvfrom(1024)
            message = message.decode().split()
            # checks if it is a hello message
            if message[0] == "HELLO":
                # checks if the account that this hello message
                # is sent from is online
                if message[1] in tcpThreads:
                    # resets the timeout for that peer since the hello message is received
                    tcpThreads[message[1]].resetTimeout()
                    print("Hello is received from " + message[1])
                    logging.info(
                        "Received from " + clientAddress[0] + ":" + str(clientAddress[1]) + " -> " + " ".join(message))
tcpSocket.close()
