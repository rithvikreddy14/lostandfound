import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'a_strong_secret_key_that_should_be_changed')
    MONGO_URI = os.environ.get('MONGO_URI', "mongodb+srv://rithvikreddy003:Rithvik.14@majorproject.acfksho.mongodb.net/")
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your_jwt_super_secret_key')
    
    # We no longer need local upload folders, but keeping it as a safe fallback
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'uploads')
    
    LOCATIONIQ_API_KEY = os.environ.get('LOCATIONIQ_API_KEY')
    
    IMAGE_MODEL_PATH = os.path.join(os.getcwd(), 'ai_models', 'saved_models', 'image_model.h5')
    TEXT_MODEL_PATH = os.path.join(os.getcwd(), 'ai_models', 'saved_models', 'text_model.pkl')
    
    # Email Configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = os.environ.get('MAIL_PORT', 587)
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')

    # Cloudinary Configuration
    CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME')
    CLOUDINARY_API_KEY = os.environ.get('CLOUDINARY_API_KEY')
    CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET')