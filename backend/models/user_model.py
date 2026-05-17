from pymongo import MongoClient
from bson.objectid import ObjectId

class UserModel:
    def __init__(self, db):
        self.collection = db['users']

    def create_user(self, user_data):
        """Inserts a new user document into the database."""
        result = self.collection.insert_one(user_data)
        return str(result.inserted_id)

    def find_user_by_email(self, email):
        """Finds a user by their email address."""
        user = self.collection.find_one({"email": email})
        if user:
            # Convert ObjectId to string for JSON serialization
            user['_id'] = str(user['_id'])
        return user

    def find_user_by_id(self, user_id):
        """Finds a user by their unique ID."""
        user = self.collection.find_one({"_id": ObjectId(user_id)})
        if user:
            user['_id'] = str(user['_id'])
        return user

    def update_user(self, user_id, update_data):
        """Updates an existing user's profile information."""
        result = self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0

    def delete_user(self, user_id):
        """Deletes a user from the database."""
        result = self.collection.delete_one({"_id": ObjectId(user_id)})
        return result.deleted_count > 0