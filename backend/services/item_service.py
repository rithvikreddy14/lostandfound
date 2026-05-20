import os
import uuid
import json
from werkzeug.utils import secure_filename
import requests
import logging
from pymongo.errors import PyMongoError
from bson.objectid import ObjectId
import cloudinary.uploader

item_service_logger = logging.getLogger('ItemService')

class ItemService:
    def __init__(self, db_service, app):
        self.db = db_service
        self.app = app
        self.ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
        self.item_collection = db_service.items.collection

    def allowed_file(self, filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.ALLOWED_EXTENSIONS

    def save_images(self, files):
        """Saves uploaded images to Cloudinary and returns their secure URLs."""
        image_urls = []
        for file in files:
            if file and self.allowed_file(file.filename):
                try:
                    upload_result = cloudinary.uploader.upload(file)
                    image_urls.append(upload_result['secure_url'])
                except Exception as e:
                    self.app.logger.error(f"Cloudinary upload failed: {e}")
                    filename = secure_filename(str(uuid.uuid4()) + os.path.splitext(file.filename)[1])
                    file.save(os.path.join(self.app.config['UPLOAD_FOLDER'], filename))
                    image_urls.append(f"/static/uploads/{filename}")
        return image_urls
        
    def geocode_location(self, location_name):
        locationiq_key = self.app.config.get('LOCATIONIQ_API_KEY')
        if not locationiq_key or not location_name:
            return None, None
            
        try:
            url = f"https://us1.locationiq.com/v1/search.php?key={locationiq_key}&q={location_name}&format=json"
            response = requests.get(url)
            data = response.json()
            if response.status_code == 200 and data and len(data) > 0:
                return float(data[0]['lat']), float(data[0]['lon'])
        except Exception as e:
            self.app.logger.error(f"Geocoding error: {e}")
        return None, None

    def create_item(self, user_id, form_data, image_files):
        image_urls = self.save_images(image_files) if image_files else []
        
        lat, lon = None, None
        if 'latitude' in form_data and 'longitude' in form_data:
            try:
                lat, lon = float(form_data['latitude']), float(form_data['longitude'])
            except ValueError:
                pass
        elif form_data.get('location'):
             lat, lon = self.geocode_location(form_data.get('location'))

        item_data = {
            "user_id": user_id,
            "type": form_data.get('type'),
            "title": form_data.get('title'),
            "description": form_data.get('description'),
            "category": form_data.get('category'),
            "tags": json.loads(form_data.get('tags', '[]')),
            "images": image_urls,
            "location": form_data.get('location'),
            "latitude": lat,
            "longitude": lon,
            "location_geo": {"type": "Point", "coordinates": [lon, lat]} if lat and lon else None,
            "date_occurred": form_data.get('date_occurred'),
            "status": "active"
        }
        return self.db.items.create_item(item_data)

    def find_all_items(self, query=None, limit=20, offset=0):
        # CRITICAL BUG FIX: Use explicit keyword arguments so limit and skip don't get swapped!
        return self.db.items.find_all_items(query=query, limit=limit, skip=offset)