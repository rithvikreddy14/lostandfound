from sklearn.metrics.pairwise import cosine_similarity
from geopy.distance import geodesic
import numpy as np
from math import exp 
import logging
from services.email_service import send_match_notification_email 

task_logger = logging.getLogger('celery')

class MatchingAlgorithm:
    def __init__(self):
        self.NOTIFICATION_THRESHOLD = 0.69 
        self.DISPLAY_THRESHOLD = 0.6 

    def calculate_location_score(self, item1, item2):
        if item1.get('latitude') is None or item2.get('latitude') is None:
            return 0.0

        coords_1 = (item1['latitude'], item1['longitude'])
        coords_2 = (item2['latitude'], item2['longitude'])
        
        distance = geodesic(coords_1, coords_2).kilometers
        decay_constant_km = 2.0 
        
        score = exp(-(distance / decay_constant_km)**2)
        return score

    def _safe_cosine_similarity(self, embedding1, embedding2):
        emb1 = np.array(embedding1, dtype=np.float32)
        emb2 = np.array(embedding2, dtype=np.float32)
        
        if emb1.size == 0 or emb2.size == 0:
            return 0.0
        
        if emb1.shape != emb2.shape:
             task_logger.error(f"Incompatible dimensions: {emb1.shape} vs {emb2.shape}")
             return 0.0

        emb1 = emb1.reshape(1, -1)
        emb2 = emb2.reshape(1, -1)

        return cosine_similarity(emb1, emb2)[0][0]

    def calculate_match_scores(self, item1, item2):
        img1 = item1.get('embedding_image', [])
        img2 = item2.get('embedding_image', [])
        text1 = item1.get('embedding_text', [])
        text2 = item2.get('embedding_text', [])

        # --- UPDATE: Check if both items actually have images ---
        has_both_images = bool(len(img1) > 0 and len(img2) > 0)
        
        image_score = self._safe_cosine_similarity(img1, img2) if has_both_images else 0.0
        text_score = self._safe_cosine_similarity(text1, text2) 
        location_score = self.calculate_location_score(item1, item2)

        return {
            "imageScore": image_score,
            "textScore": text_score,
            "locationScore": location_score,
            "hasBothImages": has_both_images
        }
        
    def get_final_score(self, scores):
        # --- UPDATE: Dynamic weights based on image availability ---
        if scores.get('hasBothImages', False):
            # Normal matching: Image is king
            return (
                scores['imageScore'] * 0.5 +
                scores['textScore'] * 0.3 +
                scores['locationScore'] * 0.2
            )
        else:
            # No images available: Rely heavily on NLP text matching and Location
            return (
                scores['textScore'] * 0.6 +
                scores['locationScore'] * 0.4
            )

    def run_and_notify_matches(self, new_item, potential_matches, user_model, app_config):
        from services.email_service import send_match_notification_email 
        
        high_confidence_matches = []
        MATCH_THRESHOLD = self.NOTIFICATION_THRESHOLD 

        for potential_match in potential_matches:
            # REMOVED: The check that forced items to have images is gone!

            scores = self.calculate_match_scores(new_item, potential_match)
            total_score = self.get_final_score(scores)

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

                send_match_notification_email(
                    sender_item=receiver_item_for_email, 
                    receiver_item=sender_item_for_email,       
                    match=combined_scores, 
                    app_config=app_config
                )

                send_match_notification_email(
                    sender_item=sender_item_for_email,         
                    receiver_item=receiver_item_for_email, 
                    match=combined_scores, 
                    app_config=app_config
                )
                
                high_confidence_matches.append(potential_match)
                
        return high_confidence_matches

    def find_matches(self, db_service, item_id):
        main_item = db_service.items.find_item_by_id(item_id)
        if not main_item: return []

        opposite_type = 'found' if main_item['type'] == 'lost' else 'lost'
        potential_matches = db_service.items.find_all_items(query={'type': opposite_type}, limit=0)

        matches = []
        DISPLAY_THRESHOLD = self.DISPLAY_THRESHOLD

        for potential_match in potential_matches:
            # REMOVED: The image check is gone here too!
            
            scores = self.calculate_match_scores(main_item, potential_match)
            total_score = self.get_final_score(scores)

            if total_score > DISPLAY_THRESHOLD: 
                potential_match_images = potential_match.get('images', [])
                match_user = db_service.users.find_user_by_id(potential_match['user_id'])
                
                matches.append({
                    "id": str(potential_match['_id']),
                    "score": float(total_score),
                    "imageScore": float(scores['imageScore']),
                    "textScore": float(scores['textScore']),
                    "locationScore": float(scores['locationScore']),
                    "title": potential_match['title'],
                    "image": potential_match_images[0] if potential_match_images else "/static/uploads/default_avatar.jpg",
                    "user": match_user.get('name', "Anonymous User") if match_user else "Anonymous User",
                    "email": match_user.get('email', "") if match_user else ""
                })

        matches.sort(key=lambda x: x['score'], reverse=True)
        return matches