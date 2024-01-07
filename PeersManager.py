# PeersManager.py

import logging
import GUI  # Assuming that GUI is defined in ChatRoomManager module
from colorama import Fore, Style  # Assuming you are using colorama for colored output

class PeersManager:
    def __init__(self, registry_name, registry_port, tcp_client_socket):
        self.registryName = registry_name
        self.registryPort = registry_port
        self.tcpClientSocket = tcp_client_socket

    def retrieve_peers(self):
        message = "LIST-PEERS"
        logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)
        self.tcpClientSocket.send(message.encode())
        response = self.decoded_message(self.tcpClientSocket)
        logging.info("Received from " + self.registryName + " -> " + response)

        if response.startswith("Online-Peers:"):
            online_peers = response.split(": ")[1].split(", ")
            GUI.print_colored("Online Peers:", Fore.LIGHTGREEN_EX, Style.BRIGHT)
            GUI.print_colored(f"{online_peers}\n", Fore.LIGHTGREEN_EX, Style.BRIGHT)
        elif response == "No-online-peers":
            GUI.print_colored("No online peers found", Fore.LIGHTRED_EX, Style.BRIGHT)

    def search_user(self, username):
        message = "SEARCH " + username
        logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)
        self.tcpClientSocket.send(message.encode())
        response = self.decoded_message(self.tcpClientSocket).split()
        logging.info("Received from " + self.registryName + " -> " + " ".join(response))

        if response[0] == "search-success":
            GUI.print_colored(f"{username} is found successfully...\n", Fore.LIGHTGREEN_EX, Style.BRIGHT)
            return response[1]
        elif response[0] == "search-user-not-online":
            GUI.print_colored(f"{username} is not online...\n", Fore.LIGHTRED_EX, Style.BRIGHT)
            return 0
        elif response[0] == "search-user-not-found":
            GUI.print_colored(f"{username}  is not found\n", Fore.LIGHTRED_EX, Style.BRIGHT)

            return None

    def decoded_message(self,socket):
        response= socket.recv(1024).decode()
        return response
