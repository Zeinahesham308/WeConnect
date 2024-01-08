import unittest
from unittest.mock import Mock, patch
from UserManager import UserManager

class TestUserManager(unittest.TestCase):
    def setUp(self):
        self.registry_name = "MockRegistry"
        self.registry_port = 12345
        self.tcp_client_socket = Mock()
        self.user_manager = UserManager(self.registry_name, self.registry_port, self.tcp_client_socket)

    def test_create_account_success(self):
        self.tcp_client_socket.recv.return_value = b"join-success"
        with patch("builtins.print") as mock_print:
            self.user_manager.create_account("test_user", "test_password")

        mock_print.assert_called_with("Account created...")

    def test_create_account_password_not_valid(self):
        self.tcp_client_socket.recv.return_value = b"NotValid-Password"

        with patch("builtins.print") as mock_print:
            self.user_manager.create_account("test_user", "invalid_password")

        mock_print.assert_called_with("Password does not meet the criteria. Signup again or login")

    def test_create_account_user_exists(self):
        self.tcp_client_socket.recv.return_value = b"join-exist"

        with patch("builtins.print") as mock_print:
            self.user_manager.create_account("existing_user", "password123")

        mock_print.assert_called_with("Choose another username or login...")

    @patch('UserManager.UserManager.decoded_message')
    def test_login_account_exist(self, mock_decoded_message):
        mock_decoded_message.return_value = "login-success"
        result = self.user_manager.login("testUser", "testpassword", 1234)
        self.assertEqual(result, 1)

    @patch('UserManager.UserManager.decoded_message')
    def test_login_account_not_exist(self, mock_decoded_message):
        mock_decoded_message.return_value = "login-account-not-exist"
        result = self.user_manager.login("testUser", "testpassword", 1234)
        self.assertEqual(result, 0)

    @patch('UserManager.UserManager.decoded_message')
    def test_login_account_online(self, mock_decoded_message):
        mock_decoded_message.return_value = "login-online"
        result = self.user_manager.login("testUser", "testpassword", 1234)
        self.assertEqual(result, 2)

    @patch('UserManager.UserManager.decoded_message')
    def test_login_account_wrong_password(self, mock_decoded_message):
        mock_decoded_message.return_value = "login-wrong-password"
        result = self.user_manager.login("testUser", "testpassword", 1234)
        self.assertEqual(result, 3)

    @patch('UserManager.UserManager.decoded_message')  # Adjust the import path accordingly
    def test_ports_handling(self, mock_decoded_message):
        expected_port = 12345
        mock_decoded_message.return_value = expected_port
        result = self.user_manager.portsHandling()
        # Assert that the method returned the expected result
        self.assertEqual(result, expected_port)


    def test_decoded_message(self):
        # Create an instance of YourClass
        # Configure the mock to return a specific response when recv is called
        self.tcp_client_socket.recv.return_value = b"Test response"

        # Call the decoded_message method
        result = self.user_manager.decoded_message(self.tcp_client_socket)

        # Assert that the method returned the expected result
        self.assertEqual(result, "Test response")
        # Assert that the socket.recv method was called
        self.tcp_client_socket.recv.assert_called_once_with(1024)

    @patch('UserManager.logging')
    def test_logout_with_parameters(self, mock_logging):
        # Call the logout method with parameters
        username="some_username"
        peerserverport=5678
        message = "LOGOUT " + str(username) + " " + str(peerserverport)
        self.user_manager.logout(1,username , 5678)
        expected_log_message="Send to " + self.registry_name + ":" + str(self.registry_port) + " -> " + message
        mock_logging.info.assert_called_once_with(expected_log_message)

    @patch('UserManager.logging')
    def test_logout_without_parameters(self, mock_logging):
        # Call the logout method with parameters
        username = "some_username"
        peerserverport = 5678
        message = "LOGOUT"
        self.user_manager.logout(2, username, 5678)
        expected_log_message = "Send to " + self.registry_name + ":" + str(self.registry_port) + " -> " + message
        mock_logging.info.assert_called_once_with(expected_log_message)

if __name__ == '__main__':
    unittest.main()
