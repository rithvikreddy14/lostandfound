import os
import uuid
import json
from werkzeug.utils import secure_filename
import requests
import logging
from pymongo.errors import PyMongoError
from bson.objectid import ObjectId

item_service_logger = logging.getLogger('ItemService')

class ItemService:
    def __init__(self, db_service, app):
        self.db = db_service
        self.app = app
        self.ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
        self.item_collection = db_service.items.collection
        self.match_collection = db_service.db['matches'] 

    def allowed_file(self, filename):
        """Checks if the file extension is allowed."""
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.ALLOWED_EXTENSIONS

    def save_images(self, files):
        """Saves uploaded images and returns a list of their relative URLs."""
        image_urls = []
        for file in files:
            if file and self.allowed_file(file.filename):
                filename = secure_filename(str(uuid.uuid4()) + os.path.splitext(file.filename)[1])
                file.save(os.path.join(self.app.config['UPLOAD_FOLDER'], filename))
                image_urls.append(f"/static/uploads/{filename}")
        return image_urls
        
    def geocode_location(self, location_name):
        """Converts a location name to lat/lon coordinates using LocationIQ (FALLBACK)."""
        locationiq_key = self.app.config.get('LOCATIONIQ_API_KEY')
        if not locationiq_key:
            self.app.logger.error("LocationIQ API key is missing.")
            return None, None
        
        try:
            url = f"https://us1.locationiq.com/v1/search.php?key={locationiq_key}&q={location_name}&format=json&limit=1"
            response = requests.get(url)
            if response.status_code == 200 and response.json():
                data = response.json()[0]
                return float(data['lat']), float(data['lon'])
            else:
                self.app.logger.warning(f"LocationIQ geocoding failed for '{location_name}': {response.text}")
                return None, None
        except Exception as e:
            self.app.logger.error(f"Geocoding error for '{location_name}': {e}")
            return None, None

    def create_item(self, user_id, form_data, files):
        """Handles item creation, including image saving and coordinate assignment."""
        image_urls = self.save_images(files) 
        location_name = form_data.get('location')
        
        latitude, longitude = None, None
        
        try:
            latitude = float(form_data.get('latitude')) if form_data.get('latitude') else None
            longitude = float(form_data.get('longitude')) if form_data.get('longitude') else None
        except (TypeError, ValueError):
            pass
            
        if (latitude is None or longitude is None) and location_name:
            latitude, longitude = self.geocode_location(location_name)

        item_data = {
            "user_id": user_id,
            "type": form_data.get('type'),
            "title": form_data.get('title'),
            "description": form_data.get('description'),
            "category": form_data.get('category'),
            "tags": json.loads(form_data.get('tags')),
            "images": json.dumps(image_urls),
            "location": location_name,
            "latitude": latitude,
            "longitude": longitude,
            "location_geo": {"type": "Point", "coordinates": [longitude, latitude]} 
                            if longitude is not None and latitude is not None else None,
            "date_occurred": form_data.get('date_occurred'),
            "status": "active",
            "embedding_image": [],
            "embedding_text": []
        }
        
        new_item_id = self.db.items.create_item(item_data)
        return new_item_id


    def find_all_items(self, query=None, limit=20, offset=0):
        """
        Finds items using ItemModel and safely enriches them with match data.
        """
        if query is None:
            query = {}

        # 1. Fetch items using the ItemModel's method
        items_list = self.db.items.find_all_items(
            query=query, 
            limit=limit, 
            skip=offset
        )
        
        # 2. Iterate and enrich each item with match data
        enriched_items = []
        for item in items_list:
            item_id_str = item.get('_id')
            
            if not item_id_str:
                continue 

            try:
                # Query matches where this item is either the sender or receiver
                item_matches = list(self.match_collection.find({
                    "$or": [
                        {"sender_item_id": item_id_str},
                        {"receiver_item_id": item_id_str}
                    ]
                }).sort("score", -1))

                # Assign dynamic metrics (default to 0 if not found)
                item['matches'] = len(item_matches)
                item['bestMatchScore'] = item_matches[0]['score'] if item_matches else 0.0
                
            except Exception as e:
                item_service_logger.error(f"Failed to enrich item {item_id_str} with match data: {e}")
                item['matches'] = 0
                item['bestMatchScore'] = 0.0

            enriched_items.append(item)
            
        return enriched_items

    # --- NEW METHOD: Find Nearest Police Station (Used by Celery Task) ---
    def find_nearest_police_station(self, latitude: float, longitude: float):
        """
        Uses LocationIQ API (OpenStreetMap data) to find the nearest police station.
        """
        locationiq_key = self.app.config.get('LOCATIONIQ_API_KEY')
        if not locationiq_key:
            self.app.logger.error("LocationIQ API key is missing.")
            return "a local police station in your vicinity"
        
        try:
            # Reverse geocoding with amenity filter for structured search near the point.
            url = f"https://us1.locationiq.com/v1/reverse.php?key={locationiq_key}&lat={latitude}&lon={longitude}&format=json"
            
            response = requests.get(url, params={'amenity': 'police', 'limit': 1})
            data = response.json()
            
            if response.status_code == 200 and data and data.get('address'):
                address = data['address']
                
                # Check for specific police name/type first
                name = address.get('police', None)
                if name:
                    return f"{name}, {address.get('road') or address.get('city')}"
            
            # Fallback to general display name if structured fields are missing
            if data and data.get('display_name'):
                return data['display_name']
                
            return "a local police station"
                
        except Exception as e:
            self.app.logger.error(f"Error finding police station: {e}")
            return "a local police station"