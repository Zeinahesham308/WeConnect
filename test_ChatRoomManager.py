import unittest
from unittest import mock
from unittest.mock import patch,call, MagicMock
from ChatRoomManager import ChatRoomManager
from colorama import Fore, Style, init
class TestChatRoomManager(unittest.TestCase):
    def setUp(self):
        # Mock the necessary objects
        self.mock_tcp_client_socket = MagicMock()
        self.mock_login_credentials=MagicMock()
        self.mock_gui = MagicMock()
        self.chat_room_manager = ChatRoomManager("registry_name", 1234, self.mock_tcp_client_socket,self.mock_login_credentials)

    @patch('ChatRoomManager.ChatRoomManager.decoded_message')
    @patch('ChatRoomManager.GUI.print_colored')
    def test_list_chat_rooms_success(self, mock_print_function, mock_decoded_message):
        chat_rooms = ["room1", "room2"]
        mock_decoded_message.return_value = "LIST-GROUPS-SUCCESS: " + ', '.join(chat_rooms)
        self.chat_room_manager.list_chat_rooms()
        # Define the expected calls
        expected_calls = [
            call("Available Chat Rooms: ", Fore.LIGHTGREEN_EX, Style.BRIGHT),
            call(f"{chat_rooms}\n", Fore.LIGHTGREEN_EX, Style.BRIGHT)
        ]
        # Check that the calls were made in the expected order
        mock_print_function.assert_has_calls(expected_calls)

    @patch('ChatRoomManager.ChatRoomManager.decoded_message')
    @patch('ChatRoomManager.GUI.print_colored')
    def test_list_chat_rooms_no_rooms(self, mock_print_function, mock_decoded_message):

        mock_decoded_message.return_value = "No-available-rooms"
        self.chat_room_manager.list_chat_rooms()
        mock_print_function.assert_called_once_with("No Available Chat Rooms", Fore.LIGHTRED_EX, Style.BRIGHT)

    @patch('ChatRoomManager.ChatRoomManager.decoded_message')
    @patch('ChatRoomManager.GUI.print_colored')
    @patch('builtins.input', return_value='test_input')
    def test_create_chat_room_success(self, mock_input,mock_print_function, mock_decoded_message):

        mock_decoded_message.return_value = "CREATE-CHAT-ROOM-SUCCESS"
        self.chat_room_manager.create_chat_room()
        mock_print_function.assert_called_once_with("The chat room is successfully created\n", Fore.LIGHTGREEN_EX, Style.BRIGHT)

    @patch('ChatRoomManager.ChatRoomManager.decoded_message')
    @patch('ChatRoomManager.GUI.print_colored')
    @patch('builtins.input', return_value='test_input')
    def test_create_chat_room_fail(self,mock_input, mock_print_function, mock_decoded_message):
        mock_decoded_message.return_value = "CREATE-CHAT-ROOM-FAIL"
        self.chat_room_manager.create_chat_room()
        mock_print_function.assert_called_once_with("Creation of chat room failed, name is already taken\n", Fore.LIGHTRED_EX, Style.BRIGHT)

    @patch('ChatRoomManager.ChatRoomManager.decoded_message')
    @patch('ChatRoomManager.GUI.print_colored')
    def search_room_status_success(self, mock_print_function, mock_decoded_message):
        mock_decoded_message.return_value = "search-room-success"
        room_name = "test_room"
        self.chat_room_manager.search_room_status(room_name)
        mock_print_function.assert_called_once_with(f"{room_name} is found successfully...\n", Fore.LIGHTGREEN_EX, Style.BRIGHT)

    @patch('ChatRoomManager.ChatRoomManager.decoded_message')
    @patch('ChatRoomManager.GUI.print_colored')
    def search_room_status_fail(self, mock_print_function, mock_decoded_message):
        mock_decoded_message.return_value = "search-room-not-found"
        room_name="test_room"
        self.chat_room_manager.search_room_status(room_name)
        mock_print_function.assert_called_once_with(f"{room_name} is not found\n",Fore.LIGHTRED_EX, Style.BRIGHT)

    @patch('ChatRoomManager.ChatRoomManager.decoded_message')
    @patch('ChatRoomManager.logging')
    def add_room_port_success(self, mock_logging,mock_decoded_message):
        mock_decoded_message.return_value = "ROOM-PORT-ADD-SUCCESS"
        room_name = "test_room"
        room_port=12345
        self.chat_room_manager.add_room_port(room_port)
        expected_log_message = f"Room port {room_port} of user {self.mock_login_credentials[0]} added successfully!"
        mock_logging.info.assert_called_once_with(expected_log_message)

    @patch('ChatRoomManager.ChatRoomManager.decoded_message')
    @patch('ChatRoomManager.logging')
    def add_room_port_exception_fail(self, mock_logging, mock_decoded_message):
        mock_decoded_message.side_effect = Exception("Test exception")

        room_name = "test_room"
        room_port = 12345
        self.chat_room_manager.add_room_port(room_port)
        expected_log_message = "Error in add_room_port: Test exception"
        mock_logging.error.assert_called_once_with(expected_log_message)

    def test_decoded_message(self):
        # Create an instance of YourClass
        # Configure the mock to return a specific response when recv is called
        self.mock_tcp_client_socket.recv.return_value = b"Test response"

        # Call the decoded_message method
        result = self.chat_room_manager.decoded_message(self.mock_tcp_client_socket)

        # Assert that the method returned the expected result
        self.assertEqual(result, "Test response")
        # Assert that the socket.recv method was called
        self.mock_tcp_client_socket.recv.assert_called_once_with(1024)


if __name__ == '__main__':
    unittest.main()
