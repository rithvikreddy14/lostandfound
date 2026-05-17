from flask import Blueprint, request, jsonify
from ai_models.matching_algorithm import MatchingAlgorithm # Import the AI logic

# Import the necessary components lazily or pass them
def create_match_bp(db_service):
    bp = Blueprint('match_routes', __name__)
    
    # Instantiate the matcher once outside the route for efficiency
    matcher = MatchingAlgorithm()

    @bp.route('/<item_id>', methods=['GET'])
    def get_matches(item_id):
        try:
            # We call the find_matches method defined in the algorithm class
            matches = matcher.find_matches(db_service, item_id)
        except Exception as e:
            print(f"Error finding matches for {item_id}: {e}")
            matches = []
        
        # 2. Return the dynamic results
        return jsonify({"matches": matches}), 200

    return bp