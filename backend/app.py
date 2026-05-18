import os
from flask import Flask, jsonify, request, g
from flask_cors import CORS
from config import Config
from services.db_service import DatabaseService
from services.auth_service import AuthService
from services.item_service import ItemService
from functools import wraps
import json
import logging
from celery_worker import celery_app

from routes.auth_routes import create_auth_bp
from routes.item_routes import create_item_bp
from routes.match_routes import create_match_bp

def create_app():
    logging.basicConfig(level=logging.INFO)
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app)

    db_service = DatabaseService(app)
    auth_service = AuthService(db_service, app.config['JWT_SECRET_KEY'])
    item_service = ItemService(db_service, app)

    def token_required(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = request.headers.get('Authorization')
            g.user_id = None 
            if token:
                try:
                    token_value = token.split(" ")[1]
                    user_id = auth_service.decode_jwt(token_value)
                    if user_id: g.user_id = user_id
                except Exception as e:
                    logging.warning(f"Malformed token detected: {e}")
            return f(*args, **kwargs)
        return decorated

    app.register_blueprint(create_auth_bp(db_service, auth_service), url_prefix='/api/auth')
    app.register_blueprint(create_item_bp(db_service, item_service, token_required), url_prefix='/api/items')
    app.register_blueprint(create_match_bp(db_service), url_prefix='/api/matches')

    @app.route('/api/users/me', methods=['GET', 'PUT']) 
    @token_required 
    def handle_current_user():
        user_id = g.user_id 
        if not user_id: return jsonify({'message': 'Authentication required.'}), 401

        if request.method == 'GET':
            user = db_service.users.find_user_by_id(user_id)
            if user:
                total_items = db_service.items.collection.count_documents({"user_id": user_id})
                lost_items = db_service.items.collection.count_documents({"user_id": user_id, "type": "lost"})
                found_items = db_service.items.collection.count_documents({"user_id": user_id, "type": "found"})
                successful_reunions = db_service.items.collection.count_documents({"user_id": user_id, "status": "resolved"})
                
                user_stats = {
                    "totalItems": total_items, "lostItems": lost_items,
                    "foundItems": found_items, "successfulMatches": successful_reunions,
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

    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    return app


# ==========================================
# PRODUCTION INITIALIZATION (Runs for Gunicorn)
# ==========================================
app = create_app()

from ai_models.text_processor import TextProcessor
from config import Config as AppConfig 

# Initialize Text Model globally so it works on Render
if not os.path.exists(AppConfig.TEXT_MODEL_PATH):
    text_processor = TextProcessor(AppConfig.TEXT_MODEL_PATH)
    text_processor.fit_vectorizer([
        "phone", "mobile", "cell", "smartphone", "iphone", "samsung", "pixel",
        "laptop", "macbook", "dell", "hp", "charger", "cable", "headphones", 
        "earbuds", "airpods", "tablet", "watch", "smartwatch", "kindle",
        "wallet", "purse", "handbag", "backpack", "satchel", "bag", "fanny", 
        "passport", "license", "card", "id card", "keys", "keychain", "lanyard",
        "sunglasses", "glasses", "ring", "necklace", "jewelry", "watch",
        "black", "white", "silver", "gray", "red", "blue", "green", "pink",
        "leather", "canvas", "plastic", "metal", "small", "large", "new", "old",
        "broken", "cracked", "bumpy", "scratched", "initials",
        "found", "lost", "by", "near", "pro", "max", "mini", "note", "fold"
    ])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)