"""
Unified Support Agent Pipeline.
Orchestrates Intent Classification, RAG Reply Generation, and Escalation Routing.
"""

from src.intent.classifier import LLMClassifier
from src.reply.generator import ReplyGenerator
from src.escalation.decider import EscalationDecider


class SupportAgent:
    def __init__(self,
                 taxonomy_path='src/intent/taxonomy.json',
                 index_path='models/embedding_index',
                 escalation_threshold=0.60):
        print("Initializing Unified Support Agent...")
        self.classifier = LLMClassifier(taxonomy_path)
        self.reply_generator = ReplyGenerator(index_path=index_path)
        self.escalation_decider = EscalationDecider(confidence_threshold=escalation_threshold)
        print("Agent pipeline ready.")

    def process(self, message, conversation_history=None):
        """
        Processes a single message end-to-end.
        """
        # 1. Classify intent
        intent_result = self.classifier.classify(message, conversation_history)

        # 2. Draft candidate reply via RAG
        reply_result = self.reply_generator.generate(
            message=message,
            intent=intent_result.get('intent', 'other'),
            history=conversation_history
        )

        # 3. Escalation audit
        escalation_result = self.escalation_decider.decide(
            message=message,
            intent_result=intent_result,
            reply_result=reply_result,
            history=conversation_history
        )

        is_escalated = escalation_result['escalate']

        return {
            'intent': intent_result,
            'reply': {
                'reply': '[ESCALATED — Automated reply suppressed. Ticket routed to human specialist]' if is_escalated else reply_result['reply'],
                'generated_draft': reply_result['reply'],
                'retrieved_examples': reply_result.get('retrieved_examples', []),
                'confidence': reply_result.get('confidence', 0.0)
            },
            'escalation': escalation_result,
            'auto_handled': not is_escalated
        }

    def process_batch(self, examples, max_examples=None):
        """
        Processes a batch of examples for evaluation harnesses.
        """
        from tqdm import tqdm
        batch = examples[:max_examples] if max_examples else examples
        results = []

        for ex in tqdm(batch, desc="Agent Batch Processing"):
            res = self.process(
                message=ex['customer_message'],
                conversation_history=ex.get('conversation_history', [])
            )
            res['ground_truth'] = ex
            results.append(res)

        return results


if __name__ == '__main__':
    agent = SupportAgent()

    test_scenarios = [
        "How do I set up Apple Pay on my Apple Watch?",
        "My phone display is completely black and won't charge or turn on.",
        "I noticed an unauthorized charge of $49.99 on my account. Help!",
        "This is the THIRD time your update ruined my phone. Fix this immediately or I am suing!",
        "Thanks a lot, the restart fixed it!"
    ]

    print("\n" + "=" * 80)
    print("RUNNING END-TO-END PIPELINE TESTS")
    print("=" * 80)

    for msg in test_scenarios:
        print(f"\n🧑 Customer: \"{msg}\"")
        output = agent.process(msg)
        
        status = "✅ AUTO-HANDLED" if output['auto_handled'] else "🚨 ESCALATED TO HUMAN"
        print(f"Status:     {status}")
        print(f"Intent:     {output['intent']['intent']} (Conf: {output['intent']['confidence']:.2f})")
        print(f"Reply:      {output['reply']['reply']}")
        if not output['auto_handled']:
            print(f"Draft Held: \"{output['reply']['generated_draft']}\"")
            print(f"Reason:     {output['escalation']['reason']}")
        print("-" * 80)