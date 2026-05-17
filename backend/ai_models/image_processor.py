import tensorflow as tf
from tensorflow.keras.applications.resnet50 import ResNet50, preprocess_input
from tensorflow.keras.preprocessing import image
import numpy as np
from PIL import Image

class ImageProcessor:
    def __init__(self, model_path):
        # Load the pre-trained ResNet50 model without the top classification layer
        self.model = ResNet50(weights='imagenet', include_top=False, pooling='avg')

    def get_embedding(self, img_path):
        """Generates a feature vector for an image."""
        try:
            # Load and preprocess the image
            img = Image.open(img_path).resize((224, 224))
            img_array = image.img_to_array(img)
            img_array = np.expand_dims(img_array, axis=0)
            img_array = preprocess_input(img_array)

            # Get the embedding vector
            embedding = self.model.predict(img_array, verbose=0)
            return embedding.flatten()
        except Exception as e:
            print(f"Error processing image {img_path}: {e}")
            return None