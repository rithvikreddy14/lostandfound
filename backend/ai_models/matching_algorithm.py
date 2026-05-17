from sklearn.metrics.pairwise import cosine_similarity
from geopy.distance import geodesic
import numpy as np
from math import exp 
import logging
from services.email_service import send_match_notification_email 

task_logger = logging.getLogger('celery')

class MatchingAlgorithm:
    def __init__(self):
        # Threshold for matches that trigger proactive email notification
        self.NOTIFICATION_THRESHOLD = 0.69 
        # Threshold for matches that are displayed in the frontend results list
        self.DISPLAY_THRESHOLD = 0.6 

    def calculate_location_score(self, item1, item2):
        # (Location score logic remains the same)
        if item1.get('latitude') is None or item2.get('latitude') is None:
            return 0.0

        coords_1 = (item1['latitude'], item1['longitude'])
        coords_2 = (item2['latitude'], item2['longitude'])
        
        distance = geodesic(coords_1, coords_2).kilometers
        decay_constant_km = 2.0 
        
        # Exponential decay function for location proximity
        score = exp(-(distance / decay_constant_km)**2)
        
        return score

    def _safe_cosine_similarity(self, embedding1, embedding2):
        """
        Safely calculates cosine similarity, forcing float32 type and checking dimensions.
        """
        # Force conversion to NumPy array with explicit dtype
        emb1 = np.array(embedding1, dtype=np.float32)
        emb2 = np.array(embedding2, dtype=np.float32)
        
        if emb1.size == 0 or emb2.size == 0:
            return 0.0
        
        # --- CRITICAL DIMENSION CHECK FIX ---
        if emb1.shape != emb2.shape:
             task_logger.error(f"Incompatible dimensions: {emb1.shape} vs {emb2.shape}")
             return 0.0
        # ------------------------------------

        # Reshape for sklearn's check_pairwise_arrays
        emb1 = emb1.reshape(1, -1)
        emb2 = emb2.reshape(1, -1)

        return cosine_similarity(emb1, emb2)[0][0]


    def calculate_match_scores(self, item1, item2):
        """Calculates individual scores for image, text, and location."""
        
        img1 = item1.get('embedding_image', [])
        img2 = item2.get('embedding_image', [])
        text1 = item1.get('embedding_text', [])
        text2 = item2.get('embedding_text', [])

        # Comparison 1: Image to Image
        image_score = self._safe_cosine_similarity(img1, img2)
        
        # Comparison 2: Text to Text
        text_score = self._safe_cosine_similarity(text1, text2) 

        location_score = self.calculate_location_score(item1, item2)

        return {
            "imageScore": image_score,
            "textScore": text_score,
            "locationScore": location_score
        }
        
    def get_final_score(self, scores):
        """
        Calculates the weighted final score based on project analysis:
        Image (50%) + Text (30%) + Location (20%).
        """
        image_weight = 0.5
        text_weight = 0.3
        location_weight = 0.2
        
        return (
            scores['imageScore'] * image_weight +
            scores['textScore'] * text_weight +
            scores['locationScore'] * location_weight
        )


    def run_and_notify_matches(self, new_item, potential_matches, user_model, app_config):
        """Runs the matching algorithm and sends notifications for high-confidence matches."""
        
        from services.email_service import send_match_notification_email 
        
        high_confidence_matches = []
        # Use the NOTIFICATION_THRESHOLD (69%) for emailing
        MATCH_THRESHOLD = self.NOTIFICATION_THRESHOLD 

        for potential_match in potential_matches:
            if not potential_match.get('embedding_image') or not new_item.get('embedding_image'):
                continue 

            scores = self.calculate_match_scores(new_item, potential_match)
            total_score = self.get_final_score(scores)

            # --- Check against the 69% notification threshold ---
            if total_score >= MATCH_THRESHOLD:
                
                new_item_user = user_model.find_user_by_id(new_item['user_id'])
                potential_match_user = user_model.find_user_by_id(potential_match['user_id'])
                
                if not new_item_user or not potential_match_user:
                    task_logger.warning("Skipping notification: one user email is missing.")
                    continue
                
                combined_scores = {'score': float(total_score), **scores} 
                
                sender_item_for_email = new_item.copy()
                sender_item_for_email['user'] = new_item_user
                
                receiver_item_for_email = potential_match.copy()
                receiver_item_for_email['user'] = potential_match_user

                # Send email to the person who submitted the new item
                send_match_notification_email(
                    sender_item=receiver_item_for_email, 
                    receiver_item=sender_item_for_email,       
                    match=combined_scores, 
                    app_config=app_config
                )

                # Send email to the owner of the matching item
                send_match_notification_email(
                    sender_item=sender_item_for_email,         
                    receiver_item=receiver_item_for_email, 
                    match=combined_scores, 
                    app_config=app_config
                )
                
                high_confidence_matches.append(potential_match)
                
        return high_confidence_matches


    def find_matches(self, db_service, item_id):
        """
        Finds matches for a given item to be displayed in the frontend.
        Uses the lower 60% threshold.
        """
        
        main_item = db_service.items.find_item_by_id(item_id)
        if not main_item: return []

        opposite_type = 'found' if main_item['type'] == 'lost' else 'lost'
        potential_matches = db_service.items.find_all_items(query={'type': opposite_type}, limit=0)

        matches = []
        # Use the DISPLAY_THRESHOLD (60%) for frontend list
        DISPLAY_THRESHOLD = self.DISPLAY_THRESHOLD

        for potential_match in potential_matches:
            if not potential_match.get('embedding_image') or not main_item.get('embedding_image'):
                continue 
            
            scores = self.calculate_match_scores(main_item, potential_match)
            total_score = self.get_final_score(scores)

            # --- Check against the 60% display threshold ---
            if total_score > DISPLAY_THRESHOLD: 
                potential_match_images = potential_match.get('images', [])
                # NOTE: Fetching user here for display name/email as needed
                match_user = db_service.users.find_user_by_id(potential_match['user_id'])
                
                matches.append({
                    "id": str(potential_match['_id']),
                    # CRITICAL FIX: Cast all NumPy floats to native Python floats for JSON
                    "score": float(total_score),
                    "imageScore": float(scores['imageScore']),
                    "textScore": float(scores['textScore']),
                    "locationScore": float(scores['locationScore']),
                    "title": potential_match['title'],
                    "image": potential_match_images[0] if potential_match_images else "/static/uploads/default.jpg",
                    "user": match_user.get('name', "Anonymous User") if match_user else "Anonymous User",
                    "email": match_user.get('email', "") if match_user else ""
                })

        matches.sort(key=lambda x: x['score'], reverse=True)
        return matches