"""
Simple Baseline — TF-IDF Vectorizer + Logistic Regression.
Fast, classical ML text classification without neural networks or API calls.
"""

import json
import pickle
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline


class TfidfClassifier:
    def __init__(self):
        self.pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(
                max_features=10000,
                ngram_range=(1, 2),
                min_df=2,
                stop_words='english'
            )),
            ('clf', LogisticRegression(
                max_iter=1000,
                class_weight='balanced',
                random_state=42
            ))
        ])
        self.is_trained = False
        
    def train(self, messages, labels):
        self.pipeline.fit(messages, labels)
        self.is_trained = True
        
    def classify(self, message, history=None):
        if not self.is_trained:
            raise RuntimeError("TF-IDF Classifier has not been trained or loaded yet.")
            
        probs = self.pipeline.predict_proba([message])[0]
        classes = self.pipeline.classes_
        best_idx = probs.argmax()
        
        return {
            'intent': classes[best_idx],
            'confidence': round(float(probs[best_idx]), 4),
            'reasoning': f"TF-IDF + LogReg confidence {probs[best_idx]:.2f}"
        }
        
    def save(self, path='models/tfidf_classifier.pkl'):
        model_path = Path(path)
        model_path.parent.mkdir(parents=True, exist_ok=True)
        with open(model_path, 'wb') as f:
            pickle.dump(self.pipeline, f)
        print(f"Model saved to {model_path}")
        
    def load(self, path='models/tfidf_classifier.pkl'):
        model_path = Path(path)
        with open(model_path, 'rb') as f:
            self.pipeline = pickle.load(f)
        self.is_trained = True
        print(f"Loaded TF-IDF baseline model from {model_path}")


def train_tfidf_baseline(labelled_data_path='data/processed/AppleSupport/train_labelled.json'):
    with open(labelled_data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    messages = [ex['customer_message'] for ex in data]
    labels = [ex['predicted_intent'] for ex in data]
    
    clf = TfidfClassifier()
    clf.train(messages, labels)
    clf.save()
    return clf


if __name__ == '__main__':
    train_tfidf_baseline()