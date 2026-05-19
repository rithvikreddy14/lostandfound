import os
import json
import logging
from config import Config

task_logger = logging.getLogger('background_tasks')

# --- SPEED FIX: Cache models globally so they don't reload on every upload ---
_ai_models_cache = {}

def get_ai_models():
    """Loads models only once and reuses them for instant processing."""
    if not _ai_models_cache:
        from ai_models.image_processor import ImageProcessor
        from ai_models.text_processor import TextProcessor
        from ai_models.matching_algorithm import MatchingAlgorithm
        
        task_logger.info("Initializing AI Models (This only happens once)...")
        _ai_models_cache['image'] = ImageProcessor(model_path=Config.IMAGE_MODEL_PATH)
        _ai_models_cache['text'] = TextProcessor(model_path=Config.TEXT_MODEL_PATH)
        _ai_models_cache['matcher'] = MatchingAlgorithm()
        
    return _ai_models_cache['image'], _ai_models_cache['text'], _ai_models_cache['matcher']


def process_new_item(item_id):
    from app import create_app
    app = create_app()

    from services.db_service import DatabaseService

    with app.app_context():
        db_service = DatabaseService(app=app)
        
        try:
            image_processor, text_processor, matching_algorithm = get_ai_models()
        except Exception as e:
            task_logger.error(f"AI Model Initialization Failed: {e}")
            return
        
        new_item = db_service.items.find_item_by_id(item_id)
        if not new_item: return

        # Parse stringified JSON arrays if necessary
        image_urls = new_item.get('images', [])
        if isinstance(image_urls, str):
            try:
                image_urls = json.loads(image_urls)
            except:
                image_urls = []

        img_embedding = None
        text_embedding = None

        # Fetch image embedding directly from Cloudinary URL
        if isinstance(image_urls, list) and len(image_urls) > 0:
            try:
                image_url = image_urls[0]
                # If local fallback was used, adjust path
                if image_url.startswith('/static'):
                     image_url = os.path.join(app.config['UPLOAD_FOLDER'], os.path.basename(image_url))
                
                img_embedding = image_processor.get_embedding(image_url)
            except Exception as e:
                task_logger.error(f"Failed image embedding for item {item_id}: {e}")

        # Fetch text embedding
        description = new_item.get('description', '')
        if description:
            try:
                text_embedding = text_processor.get_embedding(description)
            except Exception as e:
                task_logger.error(f"Failed text embedding for item {item_id}: {e}")
        
        if (img_embedding is None or len(img_embedding) == 0) and (text_embedding is None or len(text_embedding) == 0):
            task_logger.error(f"Skipping AI match: Both text and image embeddings failed for {item_id}.")
            return

        # Save embeddings
        db_service.items.update_item(item_id, {
            'embedding_image': img_embedding.tolist() if img_embedding is not None else [],
            'embedding_text': text_embedding.tolist() if text_embedding is not None else []
        })
        task_logger.info(f"SUCCESS: Embeddings saved for item {item_id}.")
        
        new_item['embedding_image'] = img_embedding.tolist() if img_embedding is not None else []
        new_item['embedding_text'] = text_embedding.tolist() if text_embedding is not None else []

        # Find Matches using dynamic Image OR Text OR
        opposite_type = 'found' if new_item['type'] == 'lost' else 'lost'
        potential_matches_query = {
            'type': opposite_type,
            '$or': [
                {'embedding_image': {'$exists': True, '$ne': []}},
                {'embedding_text': {'$exists': True, '$ne': []}}
            ]
        }
        
        potential_matches = db_service.items.find_all_items(query=potential_matches_query, limit=0)

        high_confidence_matches = matching_algorithm.run_and_notify_matches(
            new_item, potential_matches, db_service.users, app.config
        )

        task_logger.info(f"Found {len(high_confidence_matches)} high-confidence matches.")