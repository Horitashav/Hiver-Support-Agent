"""
Data Preparation Pipeline — Ties together loading, threading, cleaning, and train/val/test splits.
"""

import argparse
import json
import random
from pathlib import Path
import pandas as pd
from tqdm import tqdm

from src.data_prep.thread_builder import build_threads, threads_to_training_examples
from src.data_prep.cleaner import clean_thread


def main():
    parser = argparse.ArgumentParser(description='Prepare data for a specific brand')
    parser.add_argument('--brand', type=str, default='AppleSupport', help='Brand author_id')
    parser.add_argument('--max-threads', type=int, default=5000, help='Max threads to process')
    args = parser.parse_args()
    
    print("Loading raw data...")
    df = pd.read_csv('data/raw/twcs.csv')
    print(f"Loaded {len(df):,} tweets")
    
    print(f"\nFiltering for brand: {args.brand}")
    brand_tweets = df[df['author_id'] == args.brand]
    
    customer_tweet_ids = brand_tweets['in_response_to_tweet_id'].dropna().unique()
    customer_tweets = df[df['tweet_id'].isin(customer_tweet_ids)]
    
    brand_tweet_ids = brand_tweets['tweet_id'].unique()
    followup_tweets = df[df['in_response_to_tweet_id'].isin(brand_tweet_ids.astype(str))]
    
    relevant = pd.concat([brand_tweets, customer_tweets, followup_tweets]).drop_duplicates(subset='tweet_id')
    print(f"Relevant tweets: {len(relevant):,}")
    
    print("\nBuilding conversation threads...")
    threads = build_threads(relevant, args.brand)
    print(f"Built {len(threads):,} threads")
    
    if len(threads) > args.max_threads:
        threads = threads[:args.max_threads]
        print(f"Limited to {args.max_threads} threads")
    
    print("\nCleaning text...")
    threads = [clean_thread(t) for t in tqdm(threads)]
    
    print("\nCreating training examples...")
    examples = threads_to_training_examples(threads)
    print(f"Created {len(examples):,} training examples")
    
    # 70% Train / 15% Validation / 15% Test
    random.seed(42)
    random.shuffle(examples)
    
    n = len(examples)
    train_end = int(0.7 * n)
    val_end = int(0.85 * n)
    
    splits = {
        'train': examples[:train_end],
        'val': examples[train_end:val_end],
        'test': examples[val_end:]
    }
    
    output_dir = Path(f'data/processed/{args.brand}')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for split_name, split_data in splits.items():
        path = output_dir / f'{split_name}.json'
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(split_data, f, indent=2, ensure_ascii=False)
        print(f"Saved {split_name}: {len(split_data)} examples -> {path}")
    
    with open(output_dir / 'threads.json', 'w', encoding='utf-8') as f:
        json.dump(threads, f, indent=2, ensure_ascii=False)
    
    print(f"\nDone! Data prepared and saved to {output_dir}")


if __name__ == '__main__':
    main()