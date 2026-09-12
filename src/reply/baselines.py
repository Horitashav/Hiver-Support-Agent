"""
Reply Generation Baselines:
1. Trivial: Most frequent brand response in the training corpus.
2. Simple: Nearest-neighbor historical response from FAISS (pure retrieval, no generation).
"""

from collections import Counter
import json
from pathlib import Path
from src.reply.embedder import EmbeddingIndex


class TrivialReplyGenerator:
    def __init__(self, train_data_path='data/processed/AppleSupport/train.json'):
        with open(Path(train_data_path), 'r', encoding='utf-8') as f:
            data = json.load(f)
        replies = [ex['brand_reply'] for ex in data]
        self.most_common = Counter(replies).most_common(1)[0][0]
        
    def generate(self, message, intent=None, history=None):
        return {
            'reply': self.most_common,
            'retrieved_examples': [],
            'confidence': 0.0,
            'method': 'trivial_most_common'
        }


class NearestNeighborReplyGenerator:
    def __init__(self, index_path='models/embedding_index'):
        self.index = EmbeddingIndex()
        self.index.load(index_path)
        
    def generate(self, message, intent=None, history=None):
        results = self.index.search(message, top_k=1)
        if results:
            match_ex, sim = results[0]
            return {
                'reply': match_ex['brand_reply'],
                'retrieved_examples': [{
                    'customer': match_ex['customer_message'],
                    'brand': match_ex['brand_reply'],
                    'similarity': round(sim, 3)
                }],
                'confidence': float(sim),
                'method': 'nearest_neighbor'
            }
        return {
            'reply': "Please send us a DM with your details so we can look into this.",
            'retrieved_examples': [],
            'confidence': 0.0,
            'method': 'nearest_neighbor_fallback'
        }