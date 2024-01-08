import logging
from colorama import Fore, Style  # Assuming you are using colorama for colored output
import GUI
import time
import socket
from socket import *
class UserManager:
    def __init__(self, registry_name, registry_port, tcp_client_socket):
        self.registryName = registry_name
        self.registryPort = registry_port
        self.tcpClientSocket = tcp_client_socket

    def create_account(self, username, password):
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
            print("Choose another username or login...")

    def login(self, username, password, peer_server_port):
        message = "LOGIN " + username + " " + password + " " + str(peer_server_port)
        logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)
        self.tcpClientSocket.send(message.encode())
        response = self.decoded_message(self.tcpClientSocket)
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

    def logout(self, option ,username,peerserverport):
        if option == 1:
            message = "LOGOUT " + str(username) + " " + str(peerserverport)
        else:
            message = "LOGOUT"

        logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)
        self.tcpClientSocket.send(message.encode())

    def portsHandling(self):
        message = "ADD-RANDOMED-PORT"
        self.tcpClientSocket.send(message.encode())
        portno = int(self.decoded_message(self.tcpClientSocket))
        return portno
    def decoded_message(self,socket):
        response= socket.recv(1024).decode()
        return response
