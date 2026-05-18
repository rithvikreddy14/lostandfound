import os
import json
import logging
from config import Config

task_logger = logging.getLogger('background_tasks')

def process_new_item(item_id):
    from app import create_app
    app = create_app()

    from services.db_service import DatabaseService
    from ai_models.image_processor import ImageProcessor
    from ai_models.text_processor import TextProcessor
    from ai_models.matching_algorithm import MatchingAlgorithm

    with app.app_context():
        db_service = DatabaseService(app=app)
        
        try:
            image_processor = ImageProcessor(model_path=Config.IMAGE_MODEL_PATH)
            text_processor = TextProcessor(model_path=Config.TEXT_MODEL_PATH)
            matching_algorithm = MatchingAlgorithm()
        except Exception as e:
            task_logger.error(f"AI Model Initialization Failed: {e}")
            return
        
        new_item = db_service.items.find_item_by_id(item_id)
        if not new_item: return

        # --- CRITICAL FIX 1: Parse the stringified JSON array into a real Python list ---
        image_urls = new_item.get('images', [])
        if isinstance(image_urls, str):
            try:
                image_urls = json.loads(image_urls)
            except:
                image_urls = []

        img_embedding = None
        text_embedding = None

        # --- CRITICAL FIX 2: Process Image correctly ---
        if isinstance(image_urls, list) and len(image_urls) > 0:
            try:
                image_url = image_urls[0]
                image_filename = os.path.basename(image_url) 
                image_path_on_disk = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
                
                print(f"DEBUG: Looking for image at {image_path_on_disk}")
                img_embedding = image_processor.get_embedding(image_path_on_disk)
                if img_embedding is not None:
                    print("DEBUG: Image Embedding Generated Successfully!")
            except Exception as e:
                task_logger.error(f"Failed image embedding for item {item_id}: {e}")

        # --- CRITICAL FIX 3: Process Text correctly ---
        description = new_item.get('description', '')
        if description:
            try:
                text_embedding = text_processor.get_embedding(description)
                # Ensure the text vectorizer didn't return an empty array
                if text_embedding is not None and len(text_embedding) > 0:
                     print("DEBUG: Text Embedding Generated Successfully!")
                else:
                     print("DEBUG: Text Embedding failed (Empty Array returned). TF-IDF might not be fitted.")
            except Exception as e:
                task_logger.error(f"Failed text embedding for item {item_id}: {e}")
        
        # Abort only if BOTH text and image generation failed
        if (img_embedding is None or len(img_embedding) == 0) and (text_embedding is None or len(text_embedding) == 0):
            task_logger.error(f"Skipping AI match: Both text and image embeddings failed for {item_id}.")
            return

        # Save to MongoDB
        db_service.items.update_item(item_id, {
            'embedding_image': img_embedding.tolist() if img_embedding is not None else [],
            'embedding_text': text_embedding.tolist() if text_embedding is not None else []
        })
        task_logger.info(f"SUCCESS: Embeddings saved for item {item_id}.")
        
        new_item['embedding_image'] = img_embedding.tolist() if img_embedding is not None else []
        new_item['embedding_text'] = text_embedding.tolist() if text_embedding is not None else []

        # Find Matches
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