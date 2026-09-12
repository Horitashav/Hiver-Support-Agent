"""
Trivial Baseline — Random Intent Classifier.
Establishes the performance floor (~12.5% for 8 intents).
"""

import json
import random
from pathlib import Path


class RandomClassifier:
    def __init__(self, taxonomy_path='src/intent/taxonomy.json'):
        taxonomy_file = Path(taxonomy_path)
        with open(taxonomy_file, 'r', encoding='utf-8') as f:
            self.taxonomy = json.load(f)
        self.intents = list(self.taxonomy.keys())
    
    def classify(self, message, history=None):
        """
        Classifies by picking uniformly at random.
        Returns interface identical to future ML/LLM classifiers.
        """
        chosen = random.choice(self.intents)
        return {
            'intent': chosen,
            'confidence': round(1.0 / len(self.intents), 4),
            'reasoning': 'Uniform random selection baseline'
        }


if __name__ == '__main__':
    clf = RandomClassifier()
    sample_query = "My iPhone battery is draining so fast"
    print("Test Random Classification:")
    print(clf.classify(sample_query))