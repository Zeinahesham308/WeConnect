import unittest
from unittest.mock import patch,call, MagicMock
from PeersManager import PeersManager
from colorama import Fore, Style

class PeersManagerTest(unittest.TestCase):

    def setUp(self):
        # Create a mock for tcpClientSocket
        self.mock_tcp_client_socket = MagicMock()
        # Create an instance of PeersManager with the mock tcpClientSocket
        self.peers_manager = PeersManager("registry_name", 1234, self.mock_tcp_client_socket)

    @patch('PeersManager.PeersManager.decoded_message')
    @patch('PeersManager.GUI.print_colored')
    def test_retrieve_peers_success(self, mock_print_function, mock_decoded_message):
        # Configure the mock to return a success response
        online_peers = ["peer1","peer2"]
        mock_decoded_message.return_value = "Online-Peers: " + ', '.join(online_peers)
        self.peers_manager.retrieve_peers()
        expected_calls = [
            call("Online Peers:", Fore.LIGHTGREEN_EX, Style.BRIGHT),
            call(f"{online_peers}\n", Fore.LIGHTGREEN_EX, Style.BRIGHT)
        ]
        mock_print_function.assert_has_calls(expected_calls)

    @patch('PeersManager.PeersManager.decoded_message')
    @patch('PeersManager.GUI.print_colored')
    def test_retrieve_peers_no_online_peers(self, mock_print_function, mock_decoded_message):
        mock_decoded_message.return_value = "No-online-peers"
        self.peers_manager.retrieve_peers()
        mock_print_function.assert_called_with("No online peers found", Fore.LIGHTRED_EX, Style.BRIGHT)


    @patch('PeersManager.PeersManager.decoded_message')
    @patch('PeersManager.GUI.print_colored')
    def test_search_user_found(self, mock_print_function, mock_decoded_message):
        mock_decoded_message.return_value= "search-success " + "ip" + ":" + "port"
        username="testpeer"
        self.peers_manager.search_user(username)
        mock_print_function.assert_called_with(f"{username} is found successfully...\n", Fore.LIGHTGREEN_EX, Style.BRIGHT)


    @patch('PeersManager.PeersManager.decoded_message')
    @patch('PeersManager.GUI.print_colored')
    def test_search_user_not_online(self, mock_print_function, mock_decoded_message):
        mock_decoded_message.return_value= "search-user-not-online"
        username="testpeer"
        self.peers_manager.search_user(username)
        mock_print_function.assert_called_with(f"{username} is not online...\n", Fore.LIGHTRED_EX, Style.BRIGHT)

    ##########################
    @patch('PeersManager.PeersManager.decoded_message')
    @patch('PeersManager.GUI.print_colored')
    def test_search_user_not_found(self, mock_print_function, mock_decoded_message):
        mock_decoded_message.return_value= "search-user-not-found"
        username="testpeer"
        self.peers_manager.search_user(username)
        mock_print_function.assert_called_with(f"{username}  is not found\n", Fore.LIGHTRED_EX, Style.BRIGHT)


    def test_decoded_message(self):
        # Create an instance of YourClass
        # Configure the mock to return a specific response when recv is called
        self.mock_tcp_client_socket.recv.return_value = b"Test response"

        # Call the decoded_message method
        result = self.peers_manager.decoded_message(self.mock_tcp_client_socket)

        # Assert that the method returned the expected result
        self.assertEqual(result, "Test response")
        # Assert that the socket.recv method was called
        self.mock_tcp_client_socket.recv.assert_called_once_with(1024)



if __name__ == '__main__':
    unittest.main()
