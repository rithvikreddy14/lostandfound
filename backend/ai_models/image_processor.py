import tensorflow as tf
# CRITICAL FIX: Switched to MobileNetV2 to prevent Render Free Tier memory crashes (OOM)
from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input
from tensorflow.keras.preprocessing import image
import numpy as np
from PIL import Image
import requests
from io import BytesIO

class ImageProcessor:
    def __init__(self, model_path):
        # Load lightweight MobileNetV2 (1280 dimensions)
        self.model = MobileNetV2(weights='imagenet', include_top=False, pooling='avg')

    def get_embedding(self, img_source):
        """Generates a feature vector for an image (Supports Cloudinary URLs AND local)."""
        try:
            # If Cloudinary URL, download it into memory first
            if img_source.startswith('http'):
                response = requests.get(img_source)
                img = Image.open(BytesIO(response.content)).resize((224, 224))
            else:
                img = Image.open(img_source).resize((224, 224))
                
            if img.mode != 'RGB':
                img = img.convert('RGB')
                
            img_array = image.img_to_array(img)
            img_array = np.expand_dims(img_array, axis=0)
            img_array = preprocess_input(img_array)

            embedding = self.model.predict(img_array, verbose=0)
            return embedding.flatten()
        except Exception as e:
            print(f"Error processing image {img_source}: {e}")
            return None