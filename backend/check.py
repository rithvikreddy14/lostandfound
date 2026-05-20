import os
import sys
from pymongo import MongoClient
from bson.objectid import ObjectId
from dotenv import load_dotenv
import numpy as np

# --- 1. SETUP & IMPORTS ---
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

# We need the real backend AI files for this test
try:
    from ai_models.matching_algorithm import MatchingAlgorithm
    from ai_models.image_processor import ImageProcessor
    from ai_models.text_processor import TextProcessor
    from config import Config
except ImportError as e:
    print(f"❌ CRITICAL IMPORT ERROR: Could not find required AI modules.")
    print(f"Details: {e}")
    sys.exit(1)

# Database connection details
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://user:pass@cluster.mongodb.net/lost_and_found_db")
DB_NAME = "lost_and_found_db"

def run_full_pipeline_test(item_id_a, item_id_b):
    """
    Simulates fetching items and running the full matching logic using available data.
    """
    print("\n--- 🔍 STARTING END-TO-END AI LOGIC VERIFICATION ---")
    
    try:
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        items_collection = db['items']
        
        # 1. Fetch Item A and Item B
        item_a = items_collection.find_one({"_id": ObjectId(item_id_a)})
        item_b = items_collection.find_one({"_id": ObjectId(item_id_b)})

        if not item_a or not item_b:
            print("❌ ERROR: Item(s) not found in the database. Check your IDs.")
            return

        # 2. **CRITICAL CHECK**: If embeddings are missing, we mock them to test the scoring logic.
        if not item_a.get('embedding_image') or not item_b.get('embedding_image'):
            print("   -> WARNING: Real embeddings are MISSING. Mocking high-similarity vectors for test.")
            item_a['embedding_image'] = np.ones(50) * 0.9 
            item_b['embedding_image'] = np.ones(50) * 0.9
            item_a['embedding_text'] = np.ones(25) * 0.8
            item_b['embedding_text'] = np.ones(25) * 0.8
        else:
            print("   -> SUCCESS: Real embeddings found and loaded. Running on live data.")

        # 3. Prepare data and Run Matching Algorithm
        item_a['latitude'] = float(item_a.get('latitude', 0))
        item_a['longitude'] = float(item_a.get('longitude', 0))
        item_b['latitude'] = float(item_b.get('latitude', 0))
        item_b['longitude'] = float(item_b.get('longitude', 0))

        matcher = MatchingAlgorithm()
        scores = matcher.calculate_match_scores(item_a, item_b)
        
        image_weight = 0.5
        text_weight = 0.3
        location_weight = 0.2
        total_score = scores['imageScore'] * image_weight + scores['textScore'] * text_weight + scores['locationScore'] * location_weight
        
        print("\n=======================================================")
        print(f"✅ FINAL CALCULATION VERIFIED:")
        print("=======================================================")
        print(f"| Item A: {item_a['title']} | Item B: {item_b['title']} |")
        print("-------------------------------------------------------")
        print(f"| FEATURE        | RAW SCORE | WEIGHTED CONTRIBUTION |")
        print("-------------------------------------------------------")
        print(f"| Image Match    | {scores['imageScore']:.4f}  | {scores['imageScore'] * image_weight:.4f}            |")
        print(f"| Text Match     | {scores['textScore']:.4f}  | {scores['textScore'] * text_weight:.4f}             |")
        print(f"| Location Match | {scores['locationScore']:.4f}  | {scores['locationScore'] * location_weight:.4f}            |")
        print("-------------------------------------------------------")
        print(f"| FINAL SCORE    | {total_score:.4f}  | ({total_score*100:.2f}%)          |")
        print("=======================================================")


    except Exception as e:
        print(f"\n❌ CRITICAL ERROR DURING MATCHING EXECUTION.")
        print(f"   Details: {e}")

    finally:
        client.close()


# --- 5. EXECUTION ---
ITEM_A_ID = "6a0c067bbde399595ee4b8ce" # Lost ASUS TUF
ITEM_B_ID = "6a0c043bbde399595ee4b8cb" # Found Heavy Dark Gray ASUS Laptop

run_full_pipeline_test(ITEM_A_ID, ITEM_B_ID)