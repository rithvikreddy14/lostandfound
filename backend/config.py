import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'a_strong_secret_key_that_should_be_changed')
    
    # === UPDATED MONGO_URI (Using your new Atlas connection string) ===
    # Note: If this still gives a timeout error, the issue is your local network/firewall blocking DNS lookups.
    MONGO_URI = os.environ.get('MONGO_URI', "mongodb+srv://rithvikreddy003:Rithvik.14@majorproject.acfksho.mongodb.net/")
    # =================================================================
    
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your_jwt_super_secret_key')
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'uploads')
    
    # Celery (Redis) Configuration
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://default:1ZyZoeveMrvbcyyRQKFLG5LyeEARSIa9@redis-18398.c99.us-east-1-4.ec2.redns.redis-cloud.com:18398')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://default:1ZyZoeveMrvbcyyRQKFLG5LyeEARSIa9@redis-18398.c99.us-east-1-4.ec2.redns.redis-cloud.com:18398')
    
    # LocationIQ API Key
    LOCATIONIQ_API_KEY = os.environ.get('LOCATIONIQ_API_KEY')
    
    # AI Model paths
    IMAGE_MODEL_PATH = os.path.join(os.getcwd(), 'ai_models', 'resnet50_weights.h5')
    TEXT_MODEL_PATH = os.path.join(os.getcwd(), 'ai_models', 'tfidf_vectorizer.pkl')

    # --- Email Configuration (Reads strictly from environment) ---
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_USE_TLS = True
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_USERNAME')