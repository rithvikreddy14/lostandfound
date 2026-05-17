import json
from bson.objectid import ObjectId
from datetime import datetime
import numpy as np
import logging

item_model_logger = logging.getLogger('ItemModel')

class ItemModel:
    def __init__(self, db):
        self.collection = db['items']
        self.db = db

    def _prepare_item_for_response(self, item):
        """Helper to ensure data types are ready for JSON serialization."""
        if not item:
            return None
        
        # 1. Convert IDs safely
        try:
            if '_id' in item: item['_id'] = str(item['_id'])
            if 'user_id' in item: item['user_id'] = str(item['user_id'])
        except Exception:
            item_model_logger.warning(f"Failed to convert item IDs for item: {item.get('_id')}")
            return None
        
        # 2. CRITICAL FIX: Robust image handling (JSON string to list)
        images_data = item.get('images')
        try:
            if isinstance(images_data, str):
                item['images'] = json.loads(images_data)
            elif images_data is None:
                item['images'] = []
            if not isinstance(item['images'], list):
                item['images'] = []
        except json.JSONDecodeError:
            item_model_logger.error(f"Image JSON decode failed for item: {item.get('_id')}")
            item['images'] = []
            
        # 3. Handle embeddings, tags, and coordinates
        item['embedding_image'] = item.get('embedding_image', [])
        item['embedding_text'] = item.get('embedding_text', [])
        item['tags'] = item.get('tags', [])
        item['latitude'] = item.get('latitude')
        item['longitude'] = item.get('longitude')
        
        # 4. Ensure date is ISO format for the frontend
        if isinstance(item.get('date_occurred'), datetime):
             item['date_occurred'] = item['date_occurred'].isoformat()
        
        return item

    def create_item(self, item_data):
        """Inserts a new item document into the database."""
        item_data['created_at'] = datetime.utcnow()
        result = self.collection.insert_one(item_data)
        return str(result.inserted_id)

    def find_all_items(self, query=None, skip=0, limit=20, sort_by="created_at", sort_order=-1):
        """Finds all items and prepares them for JSON serialization."""
        if query is None:
            query = {}
        
        items_cursor = self.collection.find(query).skip(skip).limit(limit).sort(sort_by, sort_order)
        
        items = []
        for item in items_cursor:
            try:
                prepared_item = self._prepare_item_for_response(item)
                if prepared_item:
                    items.append(prepared_item)
            except Exception as e:
                item_model_logger.error(f"CRITICAL: Failed to process item {item.get('_id')}: {e}")
                continue

        return items

    def find_item_by_id(self, item_id):
        """Finds a single item by its ID and joins it with user data."""
        try:
            item = self.collection.find_one({"_id": ObjectId(item_id)})
        except Exception:
            return None

        item = self._prepare_item_for_response(item)

        if item and 'user_id' in item:
            try:
                user = self.db['users'].find_one({"_id": ObjectId(item['user_id'])})
            except Exception:
                user = None

            if user:
                user.pop('password_hash', None)
                user['_id'] = str(user['_id'])
                item['user'] = {
                    "name": user.get('name', 'Anonymous User'),
                    "email": user.get('email', ''),
                    "avatar": user.get('avatar', '/static/uploads/default_avatar.jpg'),
                    "rating": user.get('rating', 0),
                    "verified": user.get('verified', False),
                }
            elif 'user' not in item:
                item['user'] = {
                    "name": "Deleted/Unknown User",
                    "email": "",
                    "avatar": "/static/uploads/default_avatar.jpg",
                    "rating": 0,
                    "verified": False,
                }
        
        return item

    # --- UPDATED: find_stats method to count ACTIVE lost items (requested fix) ---
    def find_stats(self):
        """Calculates and returns the stats for the dashboard."""
        total = self.collection.count_documents({})
        # FIX: Count only items that are LOST AND ACTIVE
        items_still_lost = self.collection.count_documents({"type": "lost", "status": "active"}) 
        found = self.collection.count_documents({"type": "found"})
        successful_reunions = self.collection.count_documents({"status": "resolved"})
        return {
            "total_items": total,
            "items_still_lost": items_still_lost,
            "successful_reunions": successful_reunions
        }

    def update_item(self, item_id, update_data):
        """Updates an existing item."""
        result = self.collection.update_one(
            {"_id": ObjectId(item_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0

    def delete_item(self, item_id):
        """Deletes an item from the database."""
        result = self.collection.delete_one({"_id": ObjectId(item_id)})
        return result.deleted_count > 0