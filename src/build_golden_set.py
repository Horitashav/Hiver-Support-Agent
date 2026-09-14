"""
Golden Evaluation Set Builder.
Generates a 150-example stratified evaluation dataset from the held-out test split,
seeding initial candidate labels for human review.
"""

import json
import random
import re
from collections import defaultdict
from pathlib import Path


def load_test_and_taxonomy():
    test_path = Path('data/processed/AppleSupport/test.json')
    tax_path = Path('src/intent/taxonomy.json')
    
    with open(test_path, 'r', encoding='utf-8') as f:
        test_data = json.load(f)
    with open(tax_path, 'r', encoding='utf-8') as f:
        taxonomy = json.load(f)
        
    return test_data, taxonomy


def heuristic_categorize(text):
    """Keyword heuristics to assist initial stratification from test data."""
    t = text.lower()
    if any(k in t for k in ['charge', 'refund', 'billed', 'subscription', 'apple pay', 'receipt', 'purchase', 'cost', 'dollar', '$']):
        return 'billing_inquiry'
    if any(k in t for k in ['password', 'apple id', 'icloud login', 'verification code', '2fa', 'locked out', 'sign in']):
        return 'account_access'
    if any(k in t for k in ['crack', 'shatter', 'water damage', 'broken screen', 'physical damage', 'genius bar', 'repair store']):
        return 'hardware_repair'
    if any(k in t for k in ['compatible', 'work with', 'support apple pencil', 'connector', 'usb-c']):
        return 'product_compatibility'
    if any(k in t for k in ['worst', 'rude', 'waiting for days', 'terrible service', 'unacceptable', 'complaint']):
        return 'service_complaint'
    if any(k in t for k in ['how do i', 'how to', 'where is the setting', 'can i turn on', 'set up']):
        return 'how_to'
    if any(k in t for k in ['battery', 'restart', 'reboot', 'glitch', 'freeze', 'crash', 'ios update', 'drain', 'black screen', 'wifi']):
        return 'technical_issue'
    return 'other'


def build_golden_eval_set(target_size=150, min_per_class=12):
    test_data, taxonomy = load_test_and_taxonomy()
    random.seed(42)
    random.shuffle(test_data)

    by_class = defaultdict(list)
    for ex in test_data:
        cat = heuristic_categorize(ex['customer_message'])
        by_class[cat].append(ex)

    selected = []
    seen_texts = set()

    # 1. Stratified base: minimum samples per intent class
    for intent in taxonomy.keys():
        candidates = by_class.get(intent, [])
        take_count = min(min_per_class, len(candidates))
        for item in candidates[:take_count]:
            if item['customer_message'] not in seen_texts:
                selected.append((item, intent))
                seen_texts.add(item['customer_message'])

    # 2. Add edge cases: short queries (< 35 chars)
    short_pool = [e for e in test_data if len(e['customer_message']) < 35 and e['customer_message'] not in seen_texts]
    for item in short_pool[:15]:
        cat = heuristic_categorize(item['customer_message'])
        selected.append((item, cat))
        seen_texts.add(item['customer_message'])

    # 3. Add edge cases: long queries (> 180 chars)
    long_pool = [e for e in test_data if len(e['customer_message']) > 180 and e['customer_message'] not in seen_texts]
    for item in long_pool[:15]:
        cat = heuristic_categorize(item['customer_message'])
        selected.append((item, cat))
        seen_texts.add(item['customer_message'])

    # 4. Fill remainder up to target_size
    remaining = [e for e in test_data if e['customer_message'] not in seen_texts]
    random.shuffle(remaining)
    for item in remaining:
        if len(selected) >= target_size:
            break
        cat = heuristic_categorize(item['customer_message'])
        selected.append((item, cat))
        seen_texts.add(item['customer_message'])

    # Construct final golden evaluation records
    golden_records = []
    for idx, (ex, initial_intent) in enumerate(selected, 1):
        msg = ex['customer_message']
        msg_lower = msg.lower()
        
        # Heuristic initial escalation flag for human verification
        should_esc = False
        esc_reason = "Standard automated troubleshooting"
        difficulty = "easy"

        if any(w in msg_lower for w in ['lawyer', 'sue', 'worst', 'unacceptable', 'hazard', 'fraud', 'stolen']):
            should_esc = True
            esc_reason = "High frustration or legal/security sensitivity"
            difficulty = "hard"
        elif len(msg) < 25 or len(msg) > 200:
            difficulty = "medium"

        golden_records.append({
            "id": f"eval_{idx:03d}",
            "customer_message": msg,
            "conversation_history": ex.get('conversation_history', []),
            "brand_reply_actual": ex.get('brand_reply', ''),
            "ground_truth_intent": initial_intent,
            "should_escalate": should_esc,
            "difficulty": difficulty,
            "escalation_reasoning": esc_reason,
            "ideal_reply_notes": f"Should resolve customer inquiry regarding {initial_intent} politely."
        })

    out_dir = Path('data/golden_eval')
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / 'golden_set.json'

    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(golden_records, f, indent=2, ensure_ascii=False)

    print(f"\nSuccessfully created Golden Evaluation Set with {len(golden_records)} records!")
    print(f"Saved to: {out_file}")

    from collections import Counter
    intent_dist = Counter(r['ground_truth_intent'] for r in golden_records)
    esc_dist = Counter(r['should_escalate'] for r in golden_records)
    diff_dist = Counter(r['difficulty'] for r in golden_records)

    print("\n--- Golden Set Class Distribution ---")
    for k, v in intent_dist.most_common():
        print(f"  {k:25}: {v} ({v/len(golden_records)*100:.1f}%)")

    print("\n--- Escalation Distribution ---")
    print(f"  Auto-handle (False) : {esc_dist[False]}")
    print(f"  Escalate (True)     : {esc_dist[True]}")

    print("\n--- Difficulty Distribution ---")
    for k, v in diff_dist.items():
        print(f"  {k:10}: {v}")


if __name__ == '__main__':
    build_golden_eval_set(target_size=150, min_per_class=12)