from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# Replace the URI below with your actual connection string
MONGO_URI = "mongodb+srv://rithvikreddy003:Rithvik.14@majorproject.acfksho.mongodb.net/?retryWrites=true&w=majority"

try:
    # Create a MongoDB client
    client = MongoClient(MONGO_URI)

    # Try to connect and run a test command
    client.admin.command('ping')
    print("✅ MongoDB connection successful!")

    # Optional: print available databases
    print("Databases:", client.list_database_names())

except ConnectionFailure as e:
    print("❌ MongoDB connection failed:", e)
except Exception as e:
    print("⚠️ Error:", e)
