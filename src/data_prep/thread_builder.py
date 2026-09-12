"""
Thread Builder — Reconstructs multi-turn conversation threads from flat tweets.
Handles float-string ID normalization and cycle-safe graph traversal.
"""

import pandas as pd
from collections import defaultdict


def _normalize_id(val):
    """Normalize tweet ID to clean integer string without trailing .0."""
    if pd.isna(val) or val is None or str(val).strip() == '':
        return None
    try:
        # Convert float-like strings ("12345.0") or floats to int then str
        return str(int(float(val)))
    except (ValueError, TypeError):
        return str(val).strip()


def build_threads(df, brand_id):
    """
    Build conversation threads for a specific brand.
    """
    tweet_lookup = {}
    for _, row in df.iterrows():
        tid = _normalize_id(row['tweet_id'])
        if not tid:
            continue
        tweet_lookup[tid] = {
            'tweet_id': tid,
            'author_id': str(row['author_id']),
            'text': str(row['text']) if pd.notna(row['text']) else '',
            'inbound': bool(row['inbound']),
            'in_response_to': _normalize_id(row.get('in_response_to_tweet_id')),
            'created_at': row.get('created_at', None)
        }
    
    # Map parent_id -> list of child_ids
    children = defaultdict(list)
    for tid, tweet in tweet_lookup.items():
        parent_id = tweet['in_response_to']
        if parent_id and parent_id in tweet_lookup:
            children[parent_id].append(tid)
    
    # Identify conversation roots
    roots = []
    for tid, tweet in tweet_lookup.items():
        parent_id = tweet['in_response_to']
        if parent_id is None or parent_id not in tweet_lookup:
            # Root must either be by the brand or have direct children involving the brand
            if tweet['author_id'] == brand_id:
                roots.append(tid)
            elif any(tweet_lookup.get(child, {}).get('author_id') == brand_id for child in children.get(tid, [])):
                roots.append(tid)
    
    threads = []
    visited_global = set()

    for root_id in roots:
        if root_id in visited_global:
            continue
        
        # Iterative path builder (cycle safe)
        thread = []
        curr_id = root_id
        visited_local = set()

        while curr_id and curr_id not in visited_local:
            visited_local.add(curr_id)
            visited_global.add(curr_id)
            tweet = tweet_lookup[curr_id]

            role = "agent" if tweet['author_id'] == brand_id else "customer"
            thread.append({
                'role': role,
                'text': tweet['text'],
                'tweet_id': tweet['tweet_id']
            })

            child_ids = children.get(curr_id, [])
            if not child_ids:
                break

            # Prioritize alternating roles: if current is customer, look for brand reply next
            if role == "customer":
                next_candidates = [c for c in child_ids if tweet_lookup.get(c, {}).get('author_id') == brand_id]
                curr_id = next_candidates[0] if next_candidates else child_ids[0]
            else:
                next_candidates = [c for c in child_ids if tweet_lookup.get(c, {}).get('author_id') != brand_id]
                curr_id = next_candidates[0] if next_candidates else child_ids[0]

        # Valid support thread requires at least one customer query and one agent reply
        roles = {msg['role'] for msg in thread}
        if len(thread) >= 2 and 'customer' in roles and 'agent' in roles:
            threads.append(thread)

    return threads


def threads_to_training_examples(threads):
    """
    Convert threads into training examples with context history.
    """
    examples = []
    for thread in threads:
        for i in range(len(thread)):
            if thread[i]['role'] == 'customer':
                # Find the next agent reply
                brand_reply = None
                for j in range(i + 1, len(thread)):
                    if thread[j]['role'] == 'agent':
                        brand_reply = thread[j]['text']
                        break
                
                if brand_reply:
                    examples.append({
                        'conversation_history': thread[:i],
                        'customer_message': thread[i]['text'],
                        'brand_reply': brand_reply,
                        'thread_length': len(thread)
                    })
    return examples