import joblib
import os
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

class TextProcessor:
    def __init__(self, model_path):
        self.model_path = model_path
        if os.path.exists(self.model_path):
            self.vectorizer = joblib.load(self.model_path)
        else:
            self.vectorizer = TfidfVectorizer()
            print("WARNING: TfidfVectorizer loaded without existing model file.")

    def get_embedding(self, text):
        """Generates a TF-IDF vector for a given text using the fitted model."""
        if not hasattr(self.vectorizer, 'vocabulary_'):
            return np.array([]) 
        
        vector = self.vectorizer.transform([text]).toarray().flatten()
        return vector

    def fit_vectorizer(self, corpus):
        """Fits the vectorizer on a corpus of documents and saves the model."""
        self.vectorizer.fit(corpus)
        
        # --- CRITICAL FIX: Ensure the directory exists before saving ---
        directory = os.path.dirname(self.model_path)
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            print(f"Created directory: {directory}")
        # ---------------------------------------------------------------
        
        joblib.dump(self.vectorizer, self.model_path)
        print(f"Text model fitted with {len(self.vectorizer.vocabulary_)} terms.")