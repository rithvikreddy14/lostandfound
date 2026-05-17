# services/match_service.py
from services.db_service import DatabaseService

class MatchService:
    def __init__(self, db_service):
        self.db = db_service
        
    def find_matches(self, item_id):
        """
        Retrieves mock matches for a given item.
        This will be replaced with real AI matching logic later.
        """
        # For now, let's return some mock data to make the frontend work.
        
        # Example mock data based on your frontend screenshots
        mock_matches = [
            {
                "id": "match1",
                "candidateId": "60c72b2f5f1b2c3a4b5d6f7e",
                "score": 0.89,
                "imageScore": 0.92,
                "textScore": 0.85,
                "locationScore": 0.90,
                "title": "Black iPhone Found",
                "image": "https://images.unsplash.com/photo-1592750475338-74b7b21085ab?w=300&h=200&fit=crop",
                "user": "Mike Chen"
            },
            {
                "id": "match2",
                "candidateId": "60c72b2f5f1b2c3a4b5d6f7f",
                "score": 0.76,
                "imageScore": 0.80,
                "textScore": 0.72,
                "locationScore": 0.76,
                "title": "iPhone with Case",
                "image": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=300&h=200&fit=crop",
                "user": "Emma Davis"
            },
            {
                "id": "match3",
                "candidateId": "60c72b2c3a4b5d6f80",
                "score": 0.65,
                "imageScore": 0.70,
                "textScore": 0.60,
                "locationScore": 0.65,
                "title": "Dark Phone Found",
                "image": "https://images.unsplash.com/photo-1580910051074-3eb694886505?w=300&h=200&fit=crop",
                "user": "Alex Thompson"
            }
        ]

        return mock_matches