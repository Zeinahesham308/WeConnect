from pymongo import MongoClient

class DB:
    def __init__(self):
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client['p2p-chat']

    def is_account_exist(self, username):
        return self.db.accounts.count_documents({'username': username}) > 0

    def register(self, username, password):
        account = {
            "username": username,
            "password": password
        }
        self.db.accounts.insert_one(account)

    def get_password(self, username):
        user_data = self.db.accounts.find_one({"username": username})
        return user_data["password"] if user_data else None

    def is_account_online(self, username):
        return self.db.online_peers.count_documents({"username": username}) > 0

    def user_login(self, username, ip, port):
        online_peer = {
            "username": username,
            "ip": ip,
            "port": port
        }
        self.db.online_peers.insert_one(online_peer)

    def user_logout(self, username):
        self.db.online_peers.delete_one({"username": username})

    # def get_peer_ip_port(self, username):
    #     res = self.db.online_peers.find_one({"username": username})
    #     return (res["ip"], res["port"]) if res else (None, None)


    def get_online_peers(self):
        online_peers_cursor = self.db.online_peers.find({}, {"username": 1, "_id": 0})
        online_peers_list = [peer["username"] for peer in online_peers_cursor]
        return online_peers_list

    def is_chat_room_exist(self, chatroom_name):
        return self.db.chat_rooms.count_documents({'name': chatroom_name}) > 0

    def create_chat_room(self, chatroom_name, chatroom_port):
        chat_room = {
            "name": chatroom_name,
            "port": chatroom_port,
            "members": []  # You can add more information about the chat room as needed
        }
        self.db.chat_rooms.insert_one(chat_room)

    def get_chat_rooms(self):
        chat_rooms_cursor = self.db.chat_rooms.find({}, {"name": 1, "port": 1, "_id": 0})
        chat_rooms_list = [{"name": chat_room["name"], "port": chat_room["port"]} for chat_room in chat_rooms_cursor]
        return chat_rooms_list

    def get_room_port(self, chatroom_name):
        chat_room = self.db.chat_rooms.find_one({"name": chatroom_name}, {"port": 1, "_id": 0})
        if chat_room:
            return chat_room["port"]
        else:
            # Return a default value or handle the case where the chat room doesn't exist
            return None
    def add_user_to_chat_room(self, username, chatroom_name):
        # Find the chat room by name
        # Find the chat room by name and update the members list
        result = self.db.chat_rooms.update_one(
            {"name": chatroom_name},
            {"$addToSet": {"members": username}}
        )
        return result.modified_count > 0



    def remove_user_from_chat_room(self, username, chatroom_name):
        result = self.db.chat_rooms.update_one(
            {"name": chatroom_name},
            {"$pull": {"members": username}}
        )
        return result.modified_count > 0

    def get_chat_members(self, chatroom_name):
        chat_room = self.db.chat_rooms.find_one({"name": chatroom_name})
        if chat_room:
            return chat_room.get("members", [])
        else:
            return []

    def get_peer_ip_port(self, username):
        user = self.db.users.find_one({"username": username})
        if user:
            return user.get("ip"), user.get("port")
        else:
            return None, None