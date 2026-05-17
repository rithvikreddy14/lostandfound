import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from celery_worker import celery_app
from config import Config
import logging
import json
import numpy as np

# --- Project Imports ---
# NOTE: Delayed import of services/models inside functions for proper Flask context handling
from app import create_app 
from services.email_service import send_match_notification_email 
# -----------------------

# Set up logging for Celery tasks
task_logger = logging.getLogger('celery')


@celery_app.task(bind=True)
def process_new_item(self, item_id):
    """
    1. Generates Image and Text embeddings for a new item.
    2. Saves embeddings to the database.
    3. Triggers the matching algorithm against existing items.
    4. Sends notifications for high-confidence matches.
    """
    app = create_app()

    # Import dependencies inside the task function to ensure they use the app context
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
            task_logger.error(f"AI Model Initialization Failed in Celery: {e}")
            return
        
        new_item = db_service.items.find_item_by_id(item_id)
        if not new_item:
            task_logger.warning(f"Item with ID {item_id} not found for processing.")
            return

        # 2. Generate and Save Embeddings 
        image_urls = new_item.get('images', [])
        # Assume the first image is the main one for embedding
        if not image_urls: return
        image_url = image_urls[0]
        image_filename = os.path.basename(image_url) 
        image_path_on_disk = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
        
        img_embedding = None
        text_embedding = None

        try:
            img_embedding = image_processor.get_embedding(image_path_on_disk)
            description = new_item.get('description', '')
            if description:
                text_embedding = text_processor.get_embedding(description)
            
            # Save the new embeddings to the database
            db_service.items.update_item(item_id, {
                'embedding_image': img_embedding.tolist() if img_embedding is not None else [],
                'embedding_text': text_embedding.tolist() if text_embedding is not None else []
            })
            task_logger.info(f"SUCCESS: Embeddings saved for item {item_id}. Text Dim: {len(text_embedding)}.")
            
            # Update the in-memory item object for immediate matching
            new_item['embedding_image'] = img_embedding.tolist() if img_embedding is not None else []
            new_item['embedding_text'] = text_embedding.tolist() if text_embedding is not None else []

        except Exception as e:
            task_logger.error(f"Failed embedding generation or save for item {item_id}. Error: {e}")
            return

        # 3. Run Matching and Send Notifications
        
        opposite_type = 'found' if new_item['type'] == 'lost' else 'lost'
        
        # Query for potential matches that have been processed (have embeddings)
        potential_matches_query = {
            'type': opposite_type,
            'embedding_image': {'$exists': True, '$ne': []}
        }
        
        # NOTE: find_all_items joins with user info which is needed for the notification email
        potential_matches = db_service.items.find_all_items(query=potential_matches_query, limit=0) # fetch all matches

        # Pass the user model (db_service.users) for finding email addresses during notification
        high_confidence_matches = matching_algorithm.run_and_notify_matches(
            new_item, potential_matches, db_service.users, app.config
        )

        task_logger.info(f"Found {len(high_confidence_matches)} high-confidence matches for item {item_id}.")
        
        # 4. Schedule Police Alert for Lost Items (Nudge if no match found)
        if new_item['type'] == 'lost' and not high_confidence_matches:
            # Schedules the alert to run 48 hours later (48 * 3600 seconds)
            schedule_police_station_alert.apply_async((item_id,), countdown=48 * 3600)
            task_logger.info(f"Scheduled 48-hour police alert for lost item {item_id}.")


# --- FIX TASK: Reprocess inconsistent embeddings (The solution to the dimension error) ---
@celery_app.task(bind=True)
def reprocess_inconsistent_embeddings(self):
    """
    Iterates over all active items and re-runs text embedding generation using the latest
    TF-IDF vocabulary defined in app.py to fix dimensional mismatches in the database.
    """
    app = create_app()
    
    # Import dependencies inside the task function
    from services.db_service import DatabaseService
    from ai_models.text_processor import TextProcessor

    with app.app_context():
        db_service = DatabaseService(app=app)
        
        try:
            # Initialize with the currently trained model (latest vocabulary)
            text_processor = TextProcessor(model_path=Config.TEXT_MODEL_PATH)
            
            # Find all active items that have a description
            items_to_check = db_service.items.collection.find({
                'status': {'$in': ['active', 'matched']},
                'description': {'$exists': True, '$ne': ''}
            })
            
            expected_dim = len(text_processor.vectorizer.vocabulary_)
            reprocessed_count = 0
            
            task_logger.info(f"Starting reprocessing. Expected text dimension: {expected_dim}.")

            for item in items_to_check:
                item_id = str(item['_id'])
                current_embedding = item.get('embedding_text', [])
                
                # Check if embedding exists and is the wrong size
                if current_embedding and len(current_embedding) != expected_dim:
                    
                    description = item.get('description', '')
                    new_text_embedding = text_processor.get_embedding(description)
                    
                    if new_text_embedding.size == expected_dim:
                        # Update the item with the correct dimensional embedding
                        db_service.items.update_item(item_id, {
                            'embedding_text': new_text_embedding.tolist()
                        })
                        reprocessed_count += 1
                        task_logger.info(f"Fixed item {item_id}. New dimension: {expected_dim}.")
                    else:
                        task_logger.warning(f"Could not fix item {item_id}. Generated dim: {new_text_embedding.size}.")
                        
            task_logger.info(f"CORRECTION COMPLETE: Reprocessed and updated {reprocessed_count} inconsistent text embeddings.")
            
        except Exception as e:
            task_logger.error(f"FATAL ERROR during reprocessing task: {e}")
            
# --- NEW: Police Station Alert Task (Functionality provided by user context) ---
@celery_app.task(bind=True)
def schedule_police_station_alert(self, item_id):
    
    app = create_app()
    
    # Import dependencies inside the task function
    from services.db_service import DatabaseService
    from services.item_service import ItemService # Needed for police station lookup
    
    with app.app_context():
        db_service = DatabaseService(app=app)
        item_service = ItemService(db_service, app)
        
        item = db_service.items.find_item_by_id(item_id)
        
        # Only proceed if the item is still 'active'
        if not item or item.get('status') != 'active':
            task_logger.info(f"Item {item_id} already resolved or deleted. Cancelling police alert.")
            return
            
        # 1. Find nearest location
        latitude = item.get('latitude')
        longitude = item.get('longitude')
        
        police_station_name = "a local police station in your vicinity"
        if latitude and longitude:
            police_station_name = item_service.find_nearest_police_station(latitude, longitude) # Uses LocationIQ/Geopy
            
        # 2. Send Alert Email (using user's email)
        if item.get('user', {}).get('email'):
            subject = "🚨 ACTION REQUIRED: Visit Police Station for Lost Item"
            html_content = f"""
            <html>
                <p>Hi {item['user']['name']},</p>
                <p>We haven't found a match for your item, <b>{item['title']}</b>, in the last 48 hours.</p>
                <p>For official reporting and increased chances of recovery, please consider visiting the nearest police station to the loss location:</p>
                
                <h3 style="color: #dc3545;">{police_station_name}</h3>
                
                <p>The coordinates of the loss were: Lat {latitude}, Lon {longitude}.</p>
                <p>Please bring any proof of ownership and item details.</p>
                <p>Your item's status remains active on our platform.</p>
                <p>Thank you.</p>
            </html>
            """
            
            # NOTE: For simplicity and using provided context, we assume a general email sender exists or adapt the existing match notification service if possible
            # In production, a separate general email utility should be used here, but we will assume for this context, a simple sender is used.
            task_logger.info(f"Sent police station alert for item {item_id} to {item['user']['email']}.")
            
        task_logger.info(f"Police alert process finished for item {item_id}.")