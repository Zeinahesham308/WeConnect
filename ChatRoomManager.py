import logging
from colorama import Fore, Style
from socket import socket, AF_INET, SOCK_STREAM
import GUI  # Assuming there's a GUI module

class ChatRoomManager:
    def __init__(self, registry_name, registry_port, tcp_client_socket, login_credentials):
        self.registryName = registry_name
        self.registryPort = registry_port
        self.tcpClientSocket = tcp_client_socket
        self.loginCredentials = login_credentials

    def list_chat_rooms(self):
        message = "LIST-GROUPS"
        logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)
        self.tcpClientSocket.send(message.encode())
        response = self.decoded_message(self.tcpClientSocket)
        logging.info("Received from " + self.registryName + " -> " + response)

        # Process the response to extract the list of peers
        if response.startswith("LIST-GROUPS-SUCCESS"):
            online_groups = response.split(": ")[1].split(", ")
            GUI.print_colored("Available Chat Rooms: ", Fore.LIGHTGREEN_EX, Style.BRIGHT)
            GUI.print_colored(f"{online_groups}\n", Fore.LIGHTGREEN_EX, Style.BRIGHT)
        elif response.startswith("No-available-rooms"):
            GUI.print_colored("No Available Chat Rooms", Fore.LIGHTRED_EX, Style.BRIGHT)
        else:
            print("Error parsing the response. The format may be incorrect.")


    def create_chat_room(self):
        room_name = input("Enter the chat room name: ")
        message = f"CREATE-CHAT-ROOM {room_name} {self.loginCredentials[0]} "
        logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)
        self.tcpClientSocket.send(message.encode())
        response = self.decoded_message(self.tcpClientSocket)

        logging.info("Received from " + self.registryName + " -> " + response)
        if response=="CREATE-CHAT-ROOM-SUCCESS":
            GUI.print_colored("The chat room is successfully created\n", Fore.LIGHTGREEN_EX, Style.BRIGHT)
        elif response=="CREATE-CHAT-ROOM-FAIL":
            GUI.print_colored("Creation of chat room failed, name is already taken\n", Fore.LIGHTRED_EX, Style.BRIGHT)

    def search_room_status(self, room_name):
        # a search message for the chat room is composed and sent to the database
        message = "SEARCH_ROOM " + room_name
        logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)
        self.tcpClientSocket.send(message.encode())
        response = self.decoded_message(self.tcpClientSocket)
        logging.info("Received from " + self.registryName + " -> ")
        if response == "search-room-success":
            GUI.print_colored(f"{room_name} is found successfully...\n", Fore.LIGHTGREEN_EX, Style.BRIGHT)
            return 1
        elif response == "search-room-not-found":
            GUI.print_colored(f"{room_name} is not found\n", Fore.LIGHTRED_EX, Style.BRIGHT)



    def add_room_port(self, room_port):
        try:
            # Prepare the message to send to the registry
            message = f"ADD-PORT {room_port} {self.loginCredentials[0]}"
            # Send the message to the registry
            self.tcpClientSocket.send(message.encode())
            # Receive the response if needed
            response = self.decoded_message(self.tcpClientSocket)
            if response =="ROOM-PORT-ADD-SUCCESS":
                logging.info(f"Room port{room_port} of user {self.loginCredentials[0]} added successfully!")

        except Exception as e:
            print(f"Error in add_room_port: {str(e)}")

    def decoded_message(self, socket):
        response = socket.recv(1024).decode()
        return response
