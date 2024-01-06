import unittest
from unittest.mock import MagicMock, patch,call
from db import DB  # Replace 'your_module' with the actual module name where your DB class is defined

class TestDB(unittest.TestCase):
    def setUp(self):
        # Mock MongoClient and its methods
        self.mock_client = MagicMock()
        self.mock_database = MagicMock()
        self.mock_accounts_collection = MagicMock()
        self.mock_online_peers_collection = MagicMock()
        self.mock_chat_rooms_collection = MagicMock()
        self.mock_ports_collection = MagicMock()

        # Set up the structure of the mocked database
        self.mock_client.__getitem__.return_value = self.mock_database
        self.mock_database.__getitem__.side_effect = [self.mock_accounts_collection,
                                                      self.mock_online_peers_collection,
                                                      self.mock_chat_rooms_collection,
                                                      self.mock_ports_collection]

        # Patch MongoClient to return the mocked client
        self.patcher = patch('db.MongoClient', return_value=self.mock_client)
        self.patcher.start()

        # Create an instance of the DB class with the mocked MongoClient
        self.db = DB()

    def tearDown(self):
        # Stop the patcher to clean up the changes
        self.patcher.stop()

        # Clean up the added data after each test
        self.cleanup_test_data()

    def cleanup_test_data(self):
        # Delete the test data added during the test_register method
        test_username = "test_user"
        self.db.db.accounts.delete_one({"username": test_username})

    def test_is_account_exist_when_exists(self):
        username = "existing_user"
        # Mocking the count_documents method
        with patch.object(self.db.db.accounts, 'count_documents') as mock_count_documents:
            mock_count_documents.return_value = 1  # Simulating existing user
            result = self.db.is_account_exist(username)
            mock_count_documents.assert_called_once_with({'username': username})
            self.assertTrue(result, "Expected True for an existing user")

    def test_is_account_exist_when_does_not_exist(self):
        username = "nonexistent_user"

        # Mocking the count_documents method
        with patch.object(self.db.db.accounts, 'count_documents') as mock_count_documents:
            mock_count_documents.return_value = 0  # Simulating user not existing

            result = self.db.is_account_exist(username)

            mock_count_documents.assert_called_once_with({'username': username})
            self.assertFalse(result, "Expected False for a nonexistent user")

    def test_register(self):
        username = "test_user"
        password = "test_password"

        # Mocking the insert_one method
        with patch.object(self.db.db.accounts, 'insert_one') as mock_insert_one:
            # Call the method you want to test
            self.db.register(username, password)

            # Assert the insert_one method was called with the correct account
            mock_insert_one.assert_called_once_with({"username": username, "password": password})

    def test_get_password_existing_user(self):
        username = "existing_user"
        password = "existing_password"

        # Mocking the find_one method
        with patch.object(self.db.db.accounts, 'find_one') as mock_find_one:
            mock_find_one.return_value = {"username": username, "password": password}

            result = self.db.get_password(username)

            mock_find_one.assert_called_once_with({"username": username})
            self.assertEqual(result, password, "Expected password for an existing user")

    def test_get_password_nonexistent_user(self):
        username = "nonexistent_user"

        # Mocking the find_one method
        with patch.object(self.db.db.accounts, 'find_one') as mock_find_one:
            mock_find_one.return_value = None

            result = self.db.get_password(username)

            mock_find_one.assert_called_once_with({"username": username})
            self.assertIsNone(result, "Expected None for a nonexistent user")

    def test_is_account_online_existing_user(self):
        username = "existing_user"

        # Mocking the count_documents method
        with patch.object(self.db.db.online_peers, 'count_documents') as mock_count_documents:
            mock_count_documents.return_value = 1  # Simulating online user

            result = self.db.is_account_online(username)

            mock_count_documents.assert_called_once_with({"username": username})
            self.assertTrue(result, "Expected True for an online user")

    def test_is_account_online_nonexistent_user(self):
        username = "nonexistent_user"

        # Mocking the count_documents method
        with patch.object(self.db.db.online_peers, 'count_documents') as mock_count_documents:
            mock_count_documents.return_value = 0  # Simulating offline user

            result = self.db.is_account_online(username)

            mock_count_documents.assert_called_once_with({"username": username})
            self.assertFalse(result, "Expected False for an offline user")

    def test_user_login(self):
        username = "test_user"
        ip = "127.0.0.1"
        port = 5000
        room_port = 6000

        # Mocking the insert_one method
        with patch.object(self.db.db.online_peers, 'insert_one') as mock_insert_one:
            # Call the method you want to test
            self.db.user_login(username, ip, port, room_port)

            # Assert the insert_one method was called with the correct online_peer
            mock_insert_one.assert_called_once_with({
                "username": username,
                "ip": ip,
                "port": port,
                "room_port": room_port
            })

    def test_user_logout_existing_user(self):
        username = "test_user"

        # Mocking the delete_one method
        with patch.object(self.db.db.online_peers, 'delete_one') as mock_delete_one:
            mock_delete_one.return_value.deleted_count = 1  # Simulating successful deletion

            result = self.db.user_logout(username)
            mock_delete_one.assert_called_once_with({"username": username})
            self.assertTrue(result, "Expected True for logging out an existing user")

    def test_user_logout_nonexistent_user(self):
        username = "nonexistent_user"

        # Mocking the delete_one method
        with patch.object(self.db.db.online_peers, 'delete_one') as mock_delete_one:
            mock_delete_one.return_value.deleted_count = 0  # Simulating unsuccessful deletion

            result = self.db.user_logout(username)

            mock_delete_one.assert_called_once_with({"username": username})
            self.assertFalse(result, "Expected False for logging out a nonexistent user")

    def test_get_peer_ip_port_existing_user(self):
        username = "existing_user"
        ip = "127.0.0.1"
        port = 5000

        # Mocking the find_one method
        with patch.object(self.db.db.online_peers, 'find_one') as mock_find_one:
            mock_find_one.return_value = {"username": username, "ip": ip, "port": port}

            result_ip, result_port = self.db.get_peer_ip_port(username)

            mock_find_one.assert_called_once_with({"username": username})
            self.assertEqual(result_ip, ip, "Expected IP for an existing user")
            self.assertEqual(result_port, port, "Expected port for an existing user")

    def test_get_peer_ip_port_nonexistent_user(self):
        username = "nonexistent_user"

        # Mocking the find_one method
        with patch.object(self.db.db.online_peers, 'find_one') as mock_find_one:
            mock_find_one.return_value = None

            result_ip, result_port = self.db.get_peer_ip_port(username)

            mock_find_one.assert_called_once_with({"username": username})
            self.assertIsNone(result_ip, "Expected None for a nonexistent user")
            self.assertIsNone(result_port, "Expected None for a nonexistent user")

    def test_get_online_peers(self):
        # Mocking the find method
        with patch.object(self.db.db.online_peers, 'find') as mock_find:
            mock_find.return_value = [
                {"username": "user1"},
                {"username": "user2"}
            ]

            result = self.db.get_online_peers()

            mock_find.assert_called_once_with({}, {"username": 1, "_id": 0})
            self.assertEqual(result, ["user1", "user2"], "Expected online peers list")

    def test_is_chat_room_exist_existing_room(self):
        chatroom_name = "existing_room"

        # Mocking the count_documents method
        with patch.object(self.db.db.chat_rooms, 'count_documents') as mock_count_documents:
            mock_count_documents.return_value = 1  # Simulating existing chat room

            result = self.db.is_chat_room_exist(chatroom_name)

            mock_count_documents.assert_called_once_with({'name': chatroom_name})
            self.assertTrue(result, "Expected True for an existing chat room")

    def test_is_chat_room_exist_nonexistent_room(self):
        chatroom_name = "nonexistent_room"

        # Mocking the count_documents method
        with patch.object(self.db.db.chat_rooms, 'count_documents') as mock_count_documents:
            mock_count_documents.return_value = 0  # Simulating nonexistent chat room

            result = self.db.is_chat_room_exist(chatroom_name)

            mock_count_documents.assert_called_once_with({'name': chatroom_name})
            self.assertFalse(result, "Expected False for a nonexistent chat room")

    def test_create_chat_room(self):
        chatroom_name = "test_room"

        # Mocking the insert_one method
        with patch.object(self.db.db.chat_rooms, 'insert_one') as mock_insert_one:
            # Call the method you want to test
            self.db.create_chat_room(chatroom_name)

            # Assert the insert_one method was called with the correct chat room
            mock_insert_one.assert_called_once_with({"name": chatroom_name, "members": []})

    def test_get_chat_rooms(self):
        # Mocking the find method
        with patch.object(self.db.db.chat_rooms, 'find') as mock_find:
            mock_find.return_value = [
                {"name": "room1"},
                {"name": "room2"}
            ]

            result = self.db.get_chat_rooms()

            mock_find.assert_called_once_with({}, {"name": 1, "_id": 0})
            self.assertEqual(result, ["room1", "room2"], "Expected chat rooms list")

    # def test_get_room_port_existing_room(self):
    #     chatroom_name = "existing_room"
    #     chatroom_port = 8000
    #
    #     # Mocking the find_one method
    #     with patch.object(self.db.db.chat_rooms, 'find_one') as mock_find_one:
    #         mock_find_one.return_value = {"name": chatroom_name, "port": chatroom_port}
    #
    #         result = self.db.get_room_port(chatroom_name)
    #
    #         mock_find_one.assert_called_once_with({"name": chatroom_name})
    #         self.assertEqual(result, chatroom_port, "Expected chat room port for an existing room")
    #
    # def test_get_room_port_nonexistent_room(self):
    #     chatroom_name = "nonexistent_room"
    #
    #     # Mocking the find_one method
    #     with patch.object(self.db.db.chat_rooms, 'find_one') as mock_find_one:
    #         mock_find_one.return_value = None
    #
    #         result = self.db.get_room_port(chatroom_name)
    #
    #         mock_find_one.assert_called_once_with({"name": chatroom_name})
    #         self.assertIsNone(result, "Expected None for a nonexistent chat room port")

    def test_add_user_to_chat_room_existing_room(self):
        username = "test_user"
        chatroom_name = "existing_room"

        # Mocking the update_one method
        with patch.object(self.db.db.chat_rooms, 'update_one') as mock_update_one:
            mock_update_one.return_value.modified_count = 1  # Simulating successful update

            result = self.db.add_user_to_chat_room(username, chatroom_name)

            mock_update_one.assert_called_once_with(
                {"name": chatroom_name},
                {"$addToSet": {"members": username}}
            )
            self.assertTrue(result, "Expected True for adding a user to an existing room")

    def test_add_user_to_chat_room_nonexistent_room(self):
        username = "test_user"
        chatroom_name = "nonexistent_room"

        # Mocking the update_one method
        with patch.object(self.db.db.chat_rooms, 'update_one') as mock_update_one:
            mock_update_one.return_value.modified_count = 0  # Simulating unsuccessful update

            result = self.db.add_user_to_chat_room(username, chatroom_name)

            mock_update_one.assert_called_once_with(
                {"name": chatroom_name},
                {"$addToSet": {"members": username}}
            )
            self.assertFalse(result, "Expected False for adding a user to a nonexistent room")

    def test_remove_user_from_chat_room(self):
        username = "test_user"
        chatroom_name = "test_room"

        # Mocking the update_one method
        with patch.object(self.db.db.chat_rooms, 'update_one') as mock_update_one:
            mock_update_one.return_value.modified_count = 1  # Simulating successful update

            result = self.db.remove_user_from_chat_room(username, chatroom_name)

            mock_update_one.assert_called_once_with(
                {"name": chatroom_name},
                {"$pull": {"members": username}}
            )
            self.assertTrue(result, "Expected True for removing a user from a chat room")

    # def test_remove_user_from_all_chat_rooms(self):
    #     peer_username = "test_user"
    #
    #     # Mocking the get_all_chat_rooms method
    #     with patch.object(self.db, 'get_all_chat_rooms') as mock_get_all_chat_rooms:
    #         mock_get_all_chat_rooms.return_value = ["room1", "room2"]
    #
    #         # Mocking the remove_user_from_chat_room method
    #         with patch.object(self.db, 'remove_user_from_chat_room') as mock_remove_user_from_chat_room:
    #             mock_remove_user_from_chat_room.return_value = True  # Simulating successful removal
    #
    #             self.db.remove_user_from_all_chat_rooms(peer_username)

                # Ensure that remove_user_from_chat_room is called for each chat room
                # mock_remove_user_from_chat_room.assert_called_with(peer_username, "room1")
                # mock_remove_user_from_chat_room.assert_called_with(peer_username, "room2")

    def test_get_chat_members_existing_room(self):
        chatroom_name = "existing_room"

        # Mocking the find_one method
        with patch.object(self.db.db.chat_rooms, 'find_one') as mock_find_one:
            mock_find_one.return_value = {"name": chatroom_name, "members": ["user1", "user2"]}

            result = self.db.get_chat_members(chatroom_name)

            mock_find_one.assert_called_once_with({"name": chatroom_name})
            self.assertEqual(result, ["user1", "user2"], "Expected chat room members for an existing room")

    def test_get_chat_members_nonexistent_room(self):
        chatroom_name = "nonexistent_room"

        # Mocking the find_one method
        with patch.object(self.db.db.chat_rooms, 'find_one') as mock_find_one:
            mock_find_one.return_value = None  # Simulating non-existent room

            result = self.db.get_chat_members(chatroom_name)

            mock_find_one.assert_called_once_with({"name": chatroom_name})
            self.assertEqual(result, [], "Expected empty list for a non-existent room")


    def test_is_user_in_chat_room_existing_user(self):
        username = "existing_user"
        chatroom_name = "existing_room"

        # Mocking the find_one method
        with patch.object(self.db.db.chat_rooms, 'find_one') as mock_find_one:
            mock_find_one.return_value = {"name": chatroom_name, "members": [username]}

            result = self.db.is_user_in_chat_room(username, chatroom_name)

            mock_find_one.assert_called_once_with({"name": chatroom_name})
            self.assertTrue(result, "Expected True for an existing user in a chat room")

    def test_is_user_in_chat_room_nonexistent_user(self):
        username = "nonexistent_user"
        chatroom_name = "existing_room"

        # Mocking the find_one method
        with patch.object(self.db.db.chat_rooms, 'find_one') as mock_find_one:
            mock_find_one.return_value = {"name": chatroom_name, "members": ["user1", "user2"]}

            result = self.db.is_user_in_chat_room(username, chatroom_name)

            mock_find_one.assert_called_once_with({"name": chatroom_name})
            self.assertFalse(result, "Expected False for a non-existent user in a chat room")

    def test_get_ports_for_chatroom_existing_room(self):
        chatroom_name = "existing_room"

        # Mocking the find_one method
        with patch.object(self.db.db.chat_rooms, 'find_one') as mock_find_one:
            mock_find_one.return_value = {"name": chatroom_name, "members": ["user1", "user2"]}

            # Mocking the get_peer_port method
            with patch.object(self.db, 'get_peer_port') as mock_get_peer_port:
                mock_get_peer_port.side_effect = [8080, 9090]

                result = self.db.get_ports_for_chatroom(chatroom_name)

                mock_find_one.assert_called_once_with({"name": chatroom_name})
                mock_get_peer_port.assert_has_calls([call("user1"), call("user2")], any_order=True)
                self.assertEqual(result, [8080, 9090], "Expected peer ports for an existing room")

    def test_get_ports_for_chatroom_nonexistent_room(self):
        chatroom_name = "nonexistent_room"

        # Mocking the find_one method
        with patch.object(self.db.db.chat_rooms, 'find_one') as mock_find_one:
            mock_find_one.return_value = None  # Simulating non-existent room

            result = self.db.get_ports_for_chatroom(chatroom_name)

            mock_find_one.assert_called_once_with({"name": chatroom_name})
            self.assertEqual(result, [], "Expected empty list for a non-existent room")

    def test_get_peer_port_existing_user(self):
        username = "existing_user"

        # Mocking the find_one method
        with patch.object(self.db.db.online_peers, 'find_one') as mock_find_one:
            mock_find_one.return_value = {"username": username, "port": 8080}

            result = self.db.get_peer_port(username)

            mock_find_one.assert_called_once_with({"username": username})
            self.assertEqual(result, 8080, "Expected peer port for an existing user")

    def test_get_peer_port_nonexistent_user(self):
        username = "nonexistent_user"

        # Mocking the find_one method
        with patch.object(self.db.db.online_peers, 'find_one') as mock_find_one:
            mock_find_one.return_value = None  # Simulating non-existent user

            result = self.db.get_peer_port(username)

            mock_find_one.assert_called_once_with({"username": username})
            self.assertEqual(result, None, "Expected None for a non-existent user")

    def test_get_peer_room_port_existing_user(self):
        username = "existing_user"

        # Mocking the find_one method
        with patch.object(self.db.db.online_peers, 'find_one') as mock_find_one:
            mock_find_one.return_value = {"username": username, "room_port": 8000}

            result = self.db.get_peer_room_port(username)

            mock_find_one.assert_called_once_with({"username": username})
            self.assertEqual(result, 8000, "Expected room port for an existing user")

    def test_get_peer_room_port_nonexistent_user(self):
        username = "nonexistent_user"

        # Mocking the find_one method
        with patch.object(self.db.db.online_peers, 'find_one') as mock_find_one:
            mock_find_one.return_value = None  # Simulating non-existent user

            result = self.db.get_peer_room_port(username)

            mock_find_one.assert_called_once_with({"username": username})
            self.assertEqual(result, None, "Expected None for a non-existent user")


    def test_get_peer_room_ports_for_chatroom_existing_room(self):
        chatroom_name = "existing_room"

        # Mocking the find_one method
        with patch.object(self.db.db.chat_rooms, 'find_one') as mock_find_one:
            mock_find_one.return_value = {"name": chatroom_name, "members": ["user1", "user2"]}

            # Mocking the get_peer_room_port method
            with patch.object(self.db, 'get_peer_room_port') as mock_get_peer_room_port:
                mock_get_peer_room_port.side_effect = [8000, 9000]

                result = self.db.get_peer_room_ports_for_chatroom(chatroom_name)

                mock_find_one.assert_called_once_with({"name": chatroom_name})
                mock_get_peer_room_port.assert_has_calls([call("user1"), call("user2")], any_order=True)
                self.assertEqual(result, [8000, 9000], "Expected peer room ports for an existing room")

    def test_online_peers_update_port(self):
        peer_username = "test_user"
        room_port = 8080

        # Mocking the update_one method
        with patch.object(self.db.db.online_peers, 'update_one') as mock_update_one:
            result = self.db.online_peers_update_port(peer_username, room_port)

            mock_update_one.assert_called_once_with(
                {"username": peer_username},
                {"$set": {"room_port": room_port}}
            )
            self.assertIsNone(result, "Expected None after updating room port")

    def test_remove_room_port(self):
        username = "test_user"

        # Mocking the update_one method
        with patch.object(self.db.db.online_peers, 'update_one') as mock_update_one:
            mock_update_one.return_value.modified_count = 1  # Simulating successful update

            result = self.db.remove_room_port(username)

            mock_update_one.assert_called_once_with(
                {"username": username},
                {"$set": {"room_port": None}}
            )
            self.assertTrue(result, "Expected True for removing room port")

    def test_add_randomed_port(self):
        portno = 8080

        # Mocking the insert_one method
        with patch.object(self.db.db.ports, 'insert_one') as mock_insert_one:
            self.db.add_randomed_port(portno)

            mock_insert_one.assert_called_once_with({"port": portno})

    def test_get_randomed_ports(self):
        # Mocking the find method
        with patch.object(self.db.db.ports, 'find') as mock_find:
            mock_find.return_value = [{"port": 8080}, {"port": 9090}]

            result = self.db.get_randomed_ports()

            mock_find.assert_called_once_with({}, {"port": 1, "_id": 0})
            self.assertEqual(result, [8080, 9090], "Expected randomed ports")

    def test_delete_port(self):
        portno = 8080
        # Mocking the delete_one method
        with patch.object(self.db.db.ports, 'delete_one') as mock_delete_one:
            self.db.delete_port(portno)
            mock_delete_one.assert_called_once_with({"port": portno})


if __name__ == '__main__':
    unittest.main()