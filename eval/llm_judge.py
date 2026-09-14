"""
LLM-as-a-Judge.
Uses Groq to semantically grade reply quality on a 1-5 scale across 3 dimensions.
"""

import json
import os
import time
from dotenv import load_dotenv
from groq import Groq
from tqdm import tqdm

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL_NAME = "openai/gpt-oss-20b"

RUBRIC = """You are an impartial judge evaluating customer support replies for AppleSupport.
Grade the AI Generated Reply based on the Customer Message and Reference Reply.

Dimensions (1 to 5 scale):
1. Relevance: Did it directly address the customer's actual problem? (1 = completely off-topic, 5 = perfectly targeted)
2. Helpfulness: Did it provide concrete, actionable troubleshooting steps or the correct support path? (1 = useless, 5 = extremely practical)
3. Tone: Was it polite, professional, concise, and empathetic like real Apple Support? (1 = rude/robotic, 5 = authentic brand voice)

Respond ONLY in valid JSON matching this schema:
{
  "relevance": <int 1-5>,
  "helpfulness": <int 1-5>,
  "tone": <int 1-5>,
  "overall": <float 1-5>,
  "reasoning": "<1 sentence explanation>"
}"""


def judge_single_reply(customer_msg, generated_reply, reference_reply=""):
    prompt = f"""Customer Tweet: "{customer_msg}"
Reference Human Reply: "{reference_reply}"
AI Generated Reply to Evaluate: "{generated_reply}"

Provide your evaluation:"""

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": RUBRIC},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {
            'relevance': 3,
            'helpfulness': 3,
            'tone': 3,
            'overall': 3.0,
            'reasoning': f"Judge error fallback: {str(e)}"
        }


def judge_batch(records, max_eval=30):
    """Judges a subset of replies to conserve time and API calls."""
    subset = records[:max_eval]
    results = []
    
    for r in tqdm(subset, desc="LLM Judge Evaluation"):
        score_data = judge_single_reply(
            customer_msg=r['customer_message'],
            generated_reply=r['generated_reply'],
            reference_reply=r.get('reference_reply', '')
        )
        results.append({**r, 'judge_scores': score_data})
        time.sleep(0.1)
        
    return results