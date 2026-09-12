"""
Main Reply Generator — Retrieval-Augmented Generation (RAG) using Groq.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq
from src.reply.embedder import EmbeddingIndex

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL_NAME = "openai/gpt-oss-20b"


class ReplyGenerator:
    def __init__(self, index_path='models/embedding_index'):
        self.index = EmbeddingIndex()
        self.index.load(index_path)
        
    def generate(self, message, intent='other', history=None, top_k=3):
        similar_cases = self.index.search(message, top_k=top_k)
        
        examples_blocks = []
        for i, (ex, sim) in enumerate(similar_cases, 1):
            examples_blocks.append(
                f"Reference Case {i} (Similarity: {sim:.2f}):\n"
                f"Customer: {ex['customer_message']}\n"
                f"Support Agent Reply: {ex['brand_reply']}"
            )
        examples_text = "\n\n".join(examples_blocks)

        history_text = ""
        if history and len(history) > 0:
            turns = []
            for msg in history[-4:]:
                role = "Customer" if msg['role'] == 'customer' else "Agent"
                turns.append(f"{role}: {msg['text']}")
            history_text = "Prior conversation thread:\n" + "\n".join(turns) + "\n\n"

        system_instruction = (
            "You are a helpful and professional customer support agent for AppleSupport on Twitter. "
            "Your task is to write an authentic, grounded reply to the customer's tweet. "
            "Requirements:\n"
            "- Keep it concise, friendly, and under 280 characters.\n"
            "- Mirror the tone and troubleshooting pattern shown in the provided reference examples.\n"
            "- Do not hallucinate URLs or policies.\n"
            "- Output ONLY the final reply text."
        )

        user_content = (
            f"Detected Intent: {intent}\n\n"
            f"{history_text}"
            f"Here are real historical examples of similar issues handled by AppleSupport:\n"
            f"{examples_text}\n\n"
            f"Current Customer Tweet to answer:\n"
            f'"{message}"\n\n'
            f"Write the support reply now:"
        )

        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.3,
                max_tokens=150
            )
            raw_content = response.choices[0].message.content or ""
            reply_text = raw_content.strip().strip('"')
            
            if not reply_text:
                # Fallback to the top retrieved historical reply if LLM returns blank
                reply_text = similar_cases[0][0]['brand_reply'] if similar_cases else (
                    "Thanks for reaching out. Please send us a DM with your device details and iOS version so we can help."
                )

            return {
                'reply': reply_text,
                'retrieved_examples': [
                    {
                        'customer': ex['customer_message'],
                        'brand': ex['brand_reply'],
                        'similarity': round(sim, 3)
                    }
                    for ex, sim in similar_cases
                ],
                'confidence': float(similar_cases[0][1]) if similar_cases else 0.0
            }
        except Exception as e:
            fallback = similar_cases[0][0]['brand_reply'] if similar_cases else (
                "Thanks for reaching out. Please send us a DM with your device details and iOS version so we can help."
            )
            return {
                'reply': fallback,
                'retrieved_examples': [],
                'confidence': 0.0,
                'error': str(e)
            }


if __name__ == '__main__':
    gen = ReplyGenerator()
    test_msg = "My AirPods won't connect to my Mac after the latest update"
    print(f"\nCustomer: {test_msg}")
    res = gen.generate(test_msg, intent='technical_issue')
    print(f"\nGenerated Reply:\n{res['reply']}")
    print(f"\nTop Retrieved Similarity: {res['confidence']}")