"""
Text Cleaner — Normalizes noisy Twitter text while preserving sentiment signals.
"""

import re


def clean_tweet(text):
    if not text or not isinstance(text, str):
        return ""
    
    # 1. Strip @mentions
    text = re.sub(r'@\w+', '', text)
    
    # 2. Replace URLs with placeholder to preserve context
    text = re.sub(r'http\S+|www\.\S+', '[URL]', text)
    
    # 3. Clean mojibake / HTML entities
    text = text.replace('â€™', "'")
    text = text.replace('â€œ', '"')
    text = text.replace('â€', '"')
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    
    # 4. Collapse extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def clean_thread(thread):
    return [
        {**msg, 'text': clean_tweet(msg['text'])}
        for msg in thread
    ]