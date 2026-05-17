import os
from flask import Flask, jsonify, request, g # IMPORT g
from flask_cors import CORS
from config import Config
from services.db_service import DatabaseService
from services.auth_service import AuthService
from services.item_service import ItemService
from functools import wraps
import json
import logging
from celery_worker import celery_app

# Import all blueprint creation functions here
from routes.auth_routes import create_auth_bp
from routes.item_routes import create_item_bp
from routes.match_routes import create_match_bp


def create_app():
    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Create a Flask app instance and load config
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app)

    # Initialize services
    db_service = DatabaseService(app)
    auth_service = AuthService(db_service, app.config['JWT_SECRET_KEY'])
    item_service = ItemService(db_service, app)

    # Decorator to protect routes
    def token_required(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = request.headers.get('Authorization')
            g.user_id = None # Initialize user_id using the flask.g object

            if token:
                try:
                    # Attempt to decode the token if it exists
                    token_value = token.split(" ")[1]
                    user_id = auth_service.decode_jwt(token_value)
                    
                    if user_id:
                        g.user_id = user_id # Set user ID on the g object
                        
                except Exception as e:
                    # Malformed token detected—log and allow request to pass with g.user_id = None
                    logging.warning(f"Malformed token detected: {e}")
            
            # Allow ALL requests to proceed. Authentication status is checked *inside* the route handler.
            return f(*args, **kwargs)
        return decorated

    # Register blueprints and pass services to them
    app.register_blueprint(create_auth_bp(db_service, auth_service), url_prefix='/api/auth')
    app.register_blueprint(create_item_bp(db_service, item_service, token_required), url_prefix='/api/items')
    app.register_blueprint(create_match_bp(db_service), url_prefix='/api/matches')

    # Endpoint to handle user data (/api/users/me) - REQUIRES AUTHENTICATION
    @app.route('/api/users/me', methods=['GET', 'PUT']) 
    @token_required 
    def handle_current_user():
        # Access user ID via g.user_id 
        user_id = g.user_id 
        
        # FINAL FIX: If this endpoint is hit, and g.user_id is None, return 401.
        if not user_id:
             return jsonify({'message': 'Authentication required.'}), 401


        if request.method == 'GET':
            user = db_service.users.find_user_by_id(user_id)
            if user:
                # Fetch user-specific stats
                total_items = db_service.items.collection.count_documents({"user_id": user_id})
                lost_items = db_service.items.collection.count_documents({"user_id": user_id, "type": "lost"})
                found_items = db_service.items.collection.count_documents({"user_id": user_id, "type": "found"})
                successful_reunions = db_service.items.collection.count_documents({"user_id": user_id, "status": "resolved"})
                
                user_stats = {
                    "totalItems": total_items,
                    "lostItems": lost_items,
                    "foundItems": found_items,
                    "successfulMatches": successful_reunions,
                    "helpedOthers": 0 
                }
                
                user.pop('password_hash', None)
                return jsonify({"user": {**user, "stats": user_stats}}), 200
            
            return jsonify({"message": "User not found"}), 404

        elif request.method == 'PUT':
            update_data = request.get_json()
            if db_service.users.update_user(user_id, update_data):
                updated_user = db_service.users.find_user_by_id(user_id)
                updated_user.pop('password_hash', None)
                return jsonify({"user": updated_user}), 200
            
            return jsonify({"message": "Failed to update user"}), 500


    # Create the uploads folder if it doesn't exist
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    return app

if __name__ == '__main__':
    from ai_models.text_processor import TextProcessor
    from config import Config as AppConfig 

    if not os.path.exists(AppConfig.TEXT_MODEL_PATH):
        text_processor = TextProcessor(AppConfig.TEXT_MODEL_PATH)
        
        # --- FINAL VERIFIED CORPUS FOR ALL REGULAR ITEMS ---
        text_processor.fit_vectorizer([
            # --- 1. Electronics & Accessories ---
            "phone", "mobile", "cell", "smartphone", "iphone", "samsung", "pixel",
            "laptop", "macbook", "dell", "hp", "charger", "cable", "headphones", 
            "earbuds", "airpods", "tablet", "watch", "smartwatch", "kindle",
            
            # --- 2. Personal Items & Bags ---
            "wallet", "purse", "handbag", "backpack", "satchel", "bag", "fanny", 
            "passport", "license", "card", "id card", "keys", "keychain", "lanyard",
            "sunglasses", "glasses", "ring", "necklace", "jewelry", "watch",
            
            # --- 3. Colors, Brands, and Descriptors ---
            "black", "white", "silver", "gray", "red", "blue", "green", "pink",
            "leather", "canvas", "plastic", "metal", "small", "large", "new", "old",
            "broken", "cracked", "bumpy", "scratched", "initials",
            "found", "lost", "by", "near", "pro", "max", "mini", "note", "fold"
        ])

    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)