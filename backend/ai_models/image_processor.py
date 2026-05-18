import tensorflow as tf
# CRITICAL FIX: Switched from ResNet50 to MobileNetV2 to prevent Render Free Tier memory crashes (OOM)
from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input
from tensorflow.keras.preprocessing import image
import numpy as np
from PIL import Image

class ImageProcessor:
    def __init__(self, model_path):
        # Load the pre-trained MobileNetV2 model (Lightweight and fast)
        self.model = MobileNetV2(weights='imagenet', include_top=False, pooling='avg')

    def get_embedding(self, img_path):
        """Generates a feature vector for an image."""
        try:
            # MobileNetV2 expects 224x224 image sizes
            img = Image.open(img_path).resize((224, 224))
            
            # Safety check: If the image is a PNG with transparency (RGBA), convert it to RGB
            # Otherwise, TensorFlow will crash when expecting 3 color channels and finding 4.
            if img.mode != 'RGB':
                img = img.convert('RGB')
                
            img_array = image.img_to_array(img)
            img_array = np.expand_dims(img_array, axis=0)
            img_array = preprocess_input(img_array)

            # Get the embedding vector
            embedding = self.model.predict(img_array, verbose=0)
            return embedding.flatten()
            
        except Exception as e:
            print(f"Error processing image {img_path}: {e}")
            return None