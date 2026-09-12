"""
Embedding Index — Converts historical customer queries into searchable dense vectors using FAISS.
"""

import json
from pathlib import Path
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


class EmbeddingIndex:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        print(f"Loading embedding model ({model_name})...")
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.examples = []
        
    def build_index(self, examples):
        self.examples = examples
        messages = [ex['customer_message'] for ex in examples]
        
        print(f"Generating dense embeddings for {len(messages):,} historical queries...")
        embeddings = self.model.encode(
            messages,
            show_progress_bar=True,
            batch_size=64
        )
        
        # Normalize vectors for fast cosine similarity via dot product
        embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        dimension = embeddings.shape[1]
        
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(embeddings.astype(np.float32))
        print(f"FAISS index built: {self.index.ntotal:,} vectors (dim={dimension})")
        
    def search(self, query_message, top_k=5):
        if self.index is None:
            raise RuntimeError("FAISS index has not been built or loaded.")
            
        query_vec = self.model.encode([query_message])
        query_vec = query_vec / np.linalg.norm(query_vec, axis=1, keepdims=True)
        
        scores, indices = self.index.search(query_vec.astype(np.float32), top_k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if 0 <= idx < len(self.examples):
                results.append((self.examples[idx], float(score)))
        return results
        
    def save(self, directory='models/embedding_index'):
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        
        faiss.write_index(self.index, str(path / 'faiss.index'))
        with open(path / 'examples.json', 'w', encoding='utf-8') as f:
            json.dump(self.examples, f, ensure_ascii=False)
        print(f"Embedding index saved to {directory}")
        
    def load(self, directory='models/embedding_index'):
        path = Path(directory)
        self.index = faiss.read_index(str(path / 'faiss.index'))
        with open(path / 'examples.json', 'r', encoding='utf-8') as f:
            self.examples = json.load(f)
        print(f"Loaded FAISS index with {self.index.ntotal:,} reference vectors")


if __name__ == '__main__':
    train_path = Path('data/processed/AppleSupport/train.json')
    with open(train_path, 'r', encoding='utf-8') as f:
        train_data = json.load(f)
        
    index = EmbeddingIndex()
    index.build_index(train_data)
    index.save()
    
    test_q = "My screen is cracked and unresponsive"
    print(f"\nTesting index retrieval for: '{test_q}'")
    hits = index.search(test_q, top_k=2)
    for i, (ex, sim) in enumerate(hits, 1):
        print(f"\n[Hit {i}] Cosine Sim: {sim:.3f}")
        print(f"Past Customer: {ex['customer_message']}")
        print(f"Past Reply:    {ex['brand_reply']}")