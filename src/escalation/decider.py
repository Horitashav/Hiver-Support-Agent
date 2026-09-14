"""
Escalation Decider — Hybrid (Deterministic Rules + LLM Evaluation) to route tickets to humans.
"""

import json
import os
import re
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL_NAME = "openai/gpt-oss-20b"


class EscalationDecider:
    # Critical keywords that require mandatory human intervention
    ESCALATION_KEYWORDS = [
        'lawyer', 'attorney', 'legal action', 'sue', 'lawsuit',
        'better business bureau', 'bbb', 'consumer protection',
        'fraud', 'unauthorized', 'stolen', 'identity theft',
        'threat', 'danger', 'safety', 'battery exploded', 'smoke',
        'reporter', 'journalist', 'media', 'going public', 'ftc', 'fcc'
    ]

    # Surface frustration and emphasis markers
    FRUSTRATION_PATTERNS = [
        r'worst\s+(customer\s+)?(service|experience|product)',
        r'never\s+(buying|using|again)',
        r'(hours|days|weeks)\s+(waiting|no\s+response)',
        r'(useless|terrible|horrible|pathetic|disgrace)',
        r'!{2,}',          # Multiple exclamation marks
        r'\?{2,}',         # Multiple question marks
        r'\b[A-Z]{4,}\b'   # Shouting in all-caps
    ]

    def __init__(self, confidence_threshold=0.60):
        self.confidence_threshold = confidence_threshold

    def decide(self, message, intent_result, reply_result=None, history=None):
        reasons = []

        # Check 1: Intent classifier confidence is low
        conf = intent_result.get('confidence', 0.0)
        if conf < self.confidence_threshold:
            reasons.append(f"Low intent confidence ({conf:.2f} < {self.confidence_threshold:.2f})")

        # Check 2: High-risk legal / safety keywords
        msg_lower = message.lower()
        found_kw = [kw for kw in self.ESCALATION_KEYWORDS if re.search(r'\b' + re.escape(kw) + r'\b', msg_lower)]
        if found_kw:
            reasons.append(f"Critical keyword match: {', '.join(found_kw)}")

        # Check 3: Frustration regex patterns
        frust_hits = [p for p in self.FRUSTRATION_PATTERNS if re.search(p, message)]
        if len(frust_hits) >= 2:
            reasons.append(f"High frustration indicators ({len(frust_hits)} patterns matched)")

        # Check 4: Conversation thread turn exhaustion (stuck in a loop)
        if history and len(history) >= 6:
            reasons.append(f"Long unresolved thread ({len(history)} turns)")

        # Check 5: Nuanced LLM analysis (only if fast rules did not trigger)
        if not reasons:
            llm_eval = self._llm_check(message, intent_result, history)
            if llm_eval.get('should_escalate', False):
                reasons.append(f"LLM judgment: {llm_eval.get('reason', 'Complex case')}")

        should_escalate = len(reasons) > 0
        return {
            'escalate': should_escalate,
            'reasons': reasons,
            'reason': reasons[0] if reasons else 'No escalation needed - standard automated resolution',
            'confidence': 0.95 if len(reasons) >= 2 else (0.80 if should_escalate else 0.85)
        }

    def _llm_check(self, message, intent_result, history=None):
        history_text = ""
        if history and len(history) > 0:
            turns = [f"{m['role'].capitalize()}: {m['text']}" for m in history[-3:]]
            history_text = "Context:\n" + "\n".join(turns) + "\n\n"

        prompt = f"""{history_text}Customer message: "{message}"
Detected Intent: {intent_result.get('intent', 'other')}

Decide if this message requires human intervention.
Consider:
1. Is there subtle sarcasm, acute emotional distress, or implied loss?
2. Is the issue too delicate or multi-faceted for a standard 1-turn reply?

Output valid JSON:
{{"should_escalate": <true/false>, "reason": "<brief justification>"}}"""

        try:
            resp = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": "You are a customer escalation specialist. Output valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                response_format={"type": "json_object"}
            )
            return json.loads(resp.choices[0].message.content)
        except Exception:
            return {'should_escalate': False, 'reason': 'LLM check skipped'}


# Baselines for evaluation comparisons
class TrivialEscalation:
    """Always escalates: 100% recall, poor precision."""
    def decide(self, message, intent_result=None, reply_result=None, history=None):
        return {
            'escalate': True,
            'reasons': ['Trivial baseline: always escalate'],
            'reason': 'Trivial baseline: always escalate',
            'confidence': 1.0
        }


class KeywordEscalation:
    """Escalates purely on basic keyword matching."""
    KEYWORDS = ['worst', 'angry', 'manager', 'lawyer', 'refund', 'unacceptable', 'terrible']

    def decide(self, message, intent_result=None, reply_result=None, history=None):
        msg_l = message.lower()
        matched = [k for k in self.KEYWORDS if k in msg_l]
        should = len(matched) > 0
        return {
            'escalate': should,
            'reasons': [f"Keyword match: {', '.join(matched)}"] if should else [],
            'reason': f"Keywords: {', '.join(matched)}" if should else 'No keyword triggers',
            'confidence': 0.85 if should else 0.70
        }


if __name__ == '__main__':
    decider = EscalationDecider()
    
    test_cases = [
        ("How do I update my iPhone to the latest iOS?", {'intent': 'how_to', 'confidence': 0.95}),
        ("My iPhone battery expanded and started smoking, this is a hazard!", {'intent': 'technical_issue', 'confidence': 0.90}),
        ("Oh wonderful, another update that bricked my device. Best company ever /s", {'intent': 'technical_issue', 'confidence': 0.75}),
        ("I will be contacting my lawyer if my account isn't restored immediately.", {'intent': 'account_access', 'confidence': 0.80})
    ]
    
    print("Testing Escalation Decider:")
    for text, intent in test_cases:
        res = decider.decide(text, intent)
        status = "🚨 ESCALATE" if res['escalate'] else "✅ AUTO-HANDLE"
        print(f"\nMessage: \"{text}\"")
        print(f"Verdict: {status} | Reason: {res['reason']}")