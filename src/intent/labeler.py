"""
Programmatic Intent Labeler using Groq.
Uses openai/gpt-oss-20b to label raw training examples.
"""

import json
import os
import re
import time
from pathlib import Path
from groq import Groq
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL_NAME = "openai/gpt-oss-20b"


def label_message(message, taxonomy):
    intent_list = "\n".join([
        f"- {name}: {details['description']}"
        for name, details in taxonomy.items()
    ])
    
    prompt = f"""Classify the following customer support message into exactly one intent.

Available intents:
{intent_list}

Customer Message: "{message}"

Respond ONLY with a valid JSON object matching this exact schema:
{{"intent": "<intent_name>", "confidence": <float 0.0-1.0>, "reasoning": "<brief justification>"}}
"""
    
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": "You are a customer support intent classifier. You output exclusively raw JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0,
        response_format={"type": "json_object"}
    )
    
    raw = response.choices[0].message.content.strip()
    return json.loads(raw)


def label_dataset(examples, taxonomy, max_examples=300):
    subset = examples[:max_examples]
    labelled = []
    
    for ex in tqdm(subset, desc=f"Labeling {len(subset)} examples"):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                res = label_message(ex['customer_message'], taxonomy)
                intent = res.get('intent', 'other')
                if intent not in taxonomy:
                    intent = 'other'
                    
                labelled.append({
                    **ex,
                    'predicted_intent': intent,
                    'intent_confidence': float(res.get('confidence', 0.0)),
                    'intent_reasoning': res.get('reasoning', '')
                })
                time.sleep(0.1)
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"\nFailed to label after {max_retries} attempts: {e}")
                    labelled.append({
                        **ex,
                        'predicted_intent': 'other',
                        'intent_confidence': 0.0,
                        'intent_reasoning': str(e)
                    })
                else:
                    time.sleep(1.0)
            
    return labelled


if __name__ == '__main__':
    with open('src/intent/taxonomy.json', 'r', encoding='utf-8') as f:
        taxonomy = json.load(f)
        
    train_path = Path('data/processed/AppleSupport/train.json')
    with open(train_path, 'r', encoding='utf-8') as f:
        train_data = json.load(f)
        
    print(f"Starting programmatic labeling of 300 examples using {MODEL_NAME}...")
    labelled_data = label_dataset(train_data, taxonomy, max_examples=300)
    
    out_path = Path('data/processed/AppleSupport/train_labelled.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(labelled_data, f, indent=2, ensure_ascii=False)
        
    print(f"\nSaved labeled data to {out_path}")
    
    from collections import Counter
    dist = Counter(x['predicted_intent'] for x in labelled_data)
    print("\nLabel Distribution:")
    for intent, count in dist.most_common():
        print(f"  {intent:25}: {count} ({count/len(labelled_data)*100:.1f}%)")