import os
from pymongo import MongoClient
from urllib.parse import urlparse
from models.user_model import UserModel
from models.item_model import ItemModel

class DatabaseService:
    def __init__(self, app):
        uri = app.config['MONGO_URI']
        parsed_uri = urlparse(uri)
        
        # Extract the database name from the URI path, with a fallback if the path is empty
        db_name = parsed_uri.path.strip('/') or 'lost_and_found_db'
        
        if not db_name:
            raise ValueError("Database name is not specified in MONGO_URI. Please ensure your URI is in the format 'mongodb+srv://user:pass@host/dbname'.")

        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.users = UserModel(self.db)
        self.items = ItemModel(self.db)
        self.init_db_indexes()

    def init_db_indexes(self):
        """Initializes indexes for efficient querying."""
        # Index for faster user lookup by email
        self.db.users.create_index("email", unique=True)
        # Index for faster item lookup and sorting
        self.db.items.create_index([("created_at", -1)])
        # Index for geospatial queries
        self.db.items.create_index([("location_geo", "2dsphere")])