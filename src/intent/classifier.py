"""
Main Intent Classifier — Groq Llama-3.3-70B based with multi-turn context.
"""

import json
import os
from pathlib import Path
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


class LLMClassifier:
    def __init__(self, taxonomy_path='src/intent/taxonomy.json'):
        with open(Path(taxonomy_path), 'r', encoding='utf-8') as f:
            self.taxonomy = json.load(f)
            
    def _build_system_prompt(self):
        intents_desc = []
        for name, details in self.taxonomy.items():
            ex_list = "\n    ".join([f'"{e}"' for e in details.get('examples', [])])
            intents_desc.append(
                f"**{name}**: {details['description']}\n  Examples:\n    {ex_list}"
            )
        taxonomy_text = "\n\n".join(intents_desc)
        
        return f"""You are a customer support intent classifier for AppleSupport.
Classify the customer message into exactly ONE of the following categories:

{taxonomy_text}

Rules:
1. Select the MOST SPECIFIC intent that describes the primary issue.
2. Consider earlier conversation turns if provided.
3. Respond ONLY with a valid JSON object.

Schema:
{{"intent": "<intent_name>", "confidence": <float 0.0-1.0>, "reasoning": "<1 sentence explanation>"}}"""

    def classify(self, message, history=None):
        user_content = ""
        if history and len(history) > 0:
            user_content += "Previous conversation context:\n"
            for msg in history[-4:]:
                role = "Customer" if msg['role'] == 'customer' else "Agent"
                user_content += f"  {role}: {msg['text']}\n"
            user_content += "\n"
            
        user_content += f"New customer message to classify: \"{message}\""
        
        try:
            response = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[
                    {"role": "system", "content": self._build_system_prompt()},
                    {"role": "user", "content": user_content}
                ],
                temperature=0,
                response_format={"type": "json_object"}
            )
            result = json.loads(response.choices[0].message.content)
            
            if result.get('intent') not in self.taxonomy:
                result['intent'] = 'other'
                result['confidence'] = 0.5
                
            return result
        except Exception as e:
            return {
                'intent': 'other',
                'confidence': 0.0,
                'reasoning': f"Classification failed: {str(e)}"
            }


if __name__ == '__main__':
    clf = LLMClassifier()
    test_msg = "I noticed an unauthorized charge of $14.99 on my Apple Card"
    print("Testing Groq LLM Classifier:")
    print(clf.classify(test_msg))