from pymongo import MongoClient
import datetime
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

    def get_peer_ip_port(self, username):
        res = self.db.online_peers.find_one({"username": username})
        return (res["ip"], res["port"]) if res else (None, None)


    ########################################################   ADDED    #######################################################################
    def insert_message(self, sender, recipient, message):
        """Insert a chat message into the database."""
        chat_collection = self.db['chat_messages']

        """['chat_messages']: This part is using indexing or key access on the self.db object to retrieve a specific collection within the database.
         In MongoDB, a database can contain multiple collections, and each collection is similar to a table in a relational database."""

        message_data = {
            'sender': sender,
            'recipient': recipient,
            'message': message,
            'timestamp': datetime.datetime.utcnow()
        }
        result = chat_collection.insert_one(message_data)
        return result.inserted_id



    def authenticate_user(self, username, password):
        """Authenticate a user by checking the username and password."""
        accounts_collection = self.db["accounts"] ####Not sure
        user =  accounts_collection.find_one({'username': username, 'password': password})
        return user is not None




    """
    
    collection=table
      
    If you want to check whether the 'accounts' collection exists or not, 
    you can use the following code to retrieve the list of collections in the current database:
    
    collection_names = self.db.list_collection_names()
    if 'accounts' in collection_names:
         print("The 'accounts' collection exists.")
    else:
         print("The 'accounts' collection does not exist.")
         
    
    """

    def create_chat_room(self, room_name, creator):
        """Create a new chat room in the 'chat_rooms' collection."""
        chat_rooms_collection = self.db['chat_rooms']
        room_data = {
            'room_name': room_name,
            'creator': creator,
            'created_at': datetime.datetime.utcnow(),
            'users': [creator]  # Include the creator in the initial user list
        }
        result = chat_rooms_collection.insert_one(room_data)
        return result.inserted_id

    def join_chat_room(self, room_id, user):
        """Add a user to the list of users in a chat room."""
        chat_rooms_collection = self.db['chat_rooms']
        chat_rooms_collection.update_one({'_id': room_id}, {'$addToSet': {'users': user}})

    def get_chat_rooms(self):
        """Retrieve a list of available chat rooms."""
        chat_rooms_collection = self.db['chat_rooms']
        return list(chat_rooms_collection.find())

    def set_peer_online(self, username):
        """Set a peer as online."""
        online_peers_collection = self.db['online_peers']
        online_peers_collection.update_one({'username': username}, {'$set': {'online': True}}, upsert=True)

    def set_peer_offline(self, username):
        """Set a peer as offline."""
        online_peers_collection = self.db['online_peers']
        online_peers_collection.update_one({'username': username}, {'$set': {'online': False}}, upsert=True)

    def get_online_peers(self):
        """Retrieve a list of online peers."""
        online_peers_collection = self.db['online_peers']
        return list(online_peers_collection.find({'online': True}))

    def send_message_to_chat_room(self, room_id, sender, message):
        """Send a message to everyone in a chat room."""
        chat_rooms_collection = self.db['chat_rooms']
        timestamp = datetime.datetime.utcnow()
        message_data = {
            'sender': sender,
            'message': message,
            'timestamp': timestamp
        }
        chat_rooms_collection.update_one({'_id': room_id}, {'$push': {'messages': message_data}})

    def get_chat_room_messages(self, room_id):
        """Retrieve messages from a chat room."""
        chat_rooms_collection = self.db['chat_rooms']
        room = chat_rooms_collection.find_one({'_id': room_id})
        if room:
            return room.get('messages', [])
        return []

    def send_private_message(self, sender, receiver, message):
        """Send a private message from one user to another."""
        private_messages_collection = self.db['private_messages']
        timestamp = datetime.datetime.utcnow()
        message_data = {
            'sender': sender,
            'receiver': receiver,
            'message': message,
            'timestamp': timestamp,
            'read': False  # Initially set to unread
        }
        private_messages_collection.insert_one(message_data)

    def get_private_messages(self, user):
        """Retrieve private messages for a user."""
        private_messages_collection = self.db['private_messages']
        messages = list(private_messages_collection.find({'receiver': user, 'read': False}))
        return messages

    def mark_private_messages_as_read(self, user):
        """Mark private messages as read for a user."""
        private_messages_collection = self.db['private_messages']
        private_messages_collection.update_many({'receiver': user, 'read': False}, {'$set': {'read': True}})