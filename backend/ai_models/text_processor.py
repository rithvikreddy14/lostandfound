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
            # Fallback (should be handled by app.py training)
            self.vectorizer = TfidfVectorizer()
            print("WARNING: TfidfVectorizer loaded without existing model file.")

    def get_embedding(self, text):
        """Generates a TF-IDF vector for a given text using the fitted model."""
        # CRITICAL FIX: Ensure the vocabulary is ready before transforming
        if not hasattr(self.vectorizer, 'vocabulary_'):
            # This should not happen if app.py ran correctly
            return np.array([]) 
        
        # Use transform method for new data. This automatically handles 
        # words outside the vocabulary by ignoring them, ensuring the output size
        # matches the fitted vocabulary size.
        vector = self.vectorizer.transform([text]).toarray().flatten()

        # NOTE: If the vector has an unexpected size (e.g., 69 vs 7), 
        # the problem is that the saved model file (the vocabulary) is being corrupted or 
        # is inconsistent. We rely on transform() to force the correct shape.
        
        return vector

    def fit_vectorizer(self, corpus):
        """Fits the vectorizer on a corpus of documents and saves the model."""
        self.vectorizer.fit(corpus)
        joblib.dump(self.vectorizer, self.model_path)
        print(f"Text model fitted with {len(self.vectorizer.vocabulary_)} features.")