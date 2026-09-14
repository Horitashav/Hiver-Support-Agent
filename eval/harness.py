"""
Main Evaluation Harness.
Executes end-to-end benchmarking against baselines and exports final comparison metrics.
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agent import SupportAgent
from src.intent.baseline_random import RandomClassifier
from src.intent.baseline_tfidf import TfidfClassifier
from src.reply.baselines import TrivialReplyGenerator, NearestNeighborReplyGenerator
from src.escalation.decider import TrivialEscalation, KeywordEscalation
from eval.metrics import evaluate_intent, evaluate_escalation, evaluate_replies
from eval.llm_judge import judge_batch
from tqdm import tqdm


def run_harness(eval_path='data/golden_eval/golden_set.json', output_dir='eval/results'):
    print(f"Loading Golden Evaluation Set from {eval_path}...")
    with open(eval_path, 'r', encoding='utf-8') as f:
        golden_set = json.load(f)
    print(f"Loaded {len(golden_set)} test instances.\n")
    
    # 1. Initialize systems
    main_agent = SupportAgent()
    random_clf = RandomClassifier()
    
    tfidf_clf = TfidfClassifier()
    tfidf_clf.load()
    
    trivial_reply = TrivialReplyGenerator()
    nn_reply = NearestNeighborReplyGenerator()
    
    trivial_esc = TrivialEscalation()
    keyword_esc = KeywordEscalation()
    
    # 2. Collect predictions
    ground_intents = [x['ground_truth_intent'] for x in golden_set]
    ground_escalate = [x['should_escalate'] for x in golden_set]
    ground_replies = [x['brand_reply_actual'] for x in golden_set]
    customer_msgs = [x['customer_message'] for x in golden_set]
    
    print("\n" + "=" * 60)
    print("RUNNING MAIN AGENT EVALUATION")
    print("=" * 60)
    
    agent_intents = []
    agent_replies = []
    agent_escalate = []
    judge_payloads = []
    
    for item in tqdm(golden_set, desc="Evaluating Main Agent"):
        res = main_agent.process(item['customer_message'], item.get('conversation_history', []))
        
        agent_intents.append(res['intent']['intent'])
        agent_escalate.append(res['escalation']['escalate'])
        draft = res['reply']['generated_draft']
        agent_replies.append(draft)
        
        judge_payloads.append({
            'customer_message': item['customer_message'],
            'generated_reply': draft,
            'reference_reply': item['brand_reply_actual']
        })
        
    print("\n" + "=" * 60)
    print("RUNNING BASELINES")
    print("=" * 60)
    
    # Trivial & Simple Intent
    rand_intents = [random_clf.classify(m)['intent'] for m in customer_msgs]
    tfidf_intents = [tfidf_clf.classify(m)['intent'] for m in customer_msgs]
    
    # Trivial & Simple Reply
    triv_replies = [trivial_reply.generate(m)['reply'] for m in customer_msgs]
    nn_replies = [nn_reply.generate(m)['reply'] for m in customer_msgs]
    
    # Trivial & Simple Escalation
    triv_esc = [trivial_esc.decide(m)['escalate'] for m in customer_msgs]
    key_esc = [keyword_esc.decide(m)['escalate'] for m in customer_msgs]
    
    # 3. Compute Metrics
    print("\n" + "=" * 60)
    print("COMPUTING FINAL METRICS")
    print("=" * 60)
    
    # Intent metrics
    main_intent_res = evaluate_intent(agent_intents, ground_intents)
    tfidf_intent_res = evaluate_intent(tfidf_intents, ground_intents)
    rand_intent_res = evaluate_intent(rand_intents, ground_intents)
    
    # Reply automated metrics
    main_reply_res = evaluate_replies(agent_replies, ground_replies)
    nn_reply_res = evaluate_replies(nn_replies, ground_replies)
    triv_reply_res = evaluate_replies(triv_replies, ground_replies)
    
    # Escalation metrics
    main_esc_res = evaluate_escalation(agent_escalate, ground_escalate)
    key_esc_res = evaluate_escalation(key_esc, ground_escalate)
    triv_esc_res = evaluate_escalation(triv_esc, ground_escalate)
    
    # LLM Judge on a representative sample of 30 items
    print("\nRunning LLM Judge semantic grading on 30 items...")
    judge_scored = judge_batch(judge_payloads, max_eval=30)
    valid_scores = [s['judge_scores'] for s in judge_scored if 'overall' in s['judge_scores']]
    
    avg_relevance = round(sum(s['relevance'] for s in valid_scores) / len(valid_scores), 2)
    avg_helpfulness = round(sum(s['helpfulness'] for s in valid_scores) / len(valid_scores), 2)
    avg_tone = round(sum(s['tone'] for s in valid_scores) / len(valid_scores), 2)
    avg_overall = round(sum(s['overall'] for s in valid_scores) / len(valid_scores), 2)
    
    # 4. Print Summary Tables
    print("\n" + "=" * 70)
    print("📊 HEADLINE EVALUATION RESULTS")
    print("=" * 70)
    
    print("\n### 1. Intent Classification Performance ###")
    print(f"{'System':<30} | {'Accuracy':<10} | {'Macro F1':<10}")
    print("-" * 56)
    print(f"{'Main Agent (LLM)':<30} | {main_intent_res['accuracy']:<10} | {main_intent_res['macro_f1']:<10}")
    print(f"{'Simple (TF-IDF + LogReg)':<30} | {tfidf_intent_res['accuracy']:<10} | {tfidf_intent_res['macro_f1']:<10}")
    print(f"{'Trivial (Random Floor)':<30} | {rand_intent_res['accuracy']:<10} | {rand_intent_res['macro_f1']:<10}")
    
    print("\n### 2. Reply Quality (BLEU Surface Overlap) ###")
    print(f"{'System':<30} | {'BLEU Mean':<10} | {'BLEU Median':<10}")
    print("-" * 56)
    print(f"{'Main Agent (RAG)':<30} | {main_reply_res['bleu_mean']:<10} | {main_reply_res['bleu_median']:<10}")
    print(f"{'Simple (Nearest Neighbor)':<30} | {nn_reply_res['bleu_mean']:<10} | {nn_reply_res['bleu_median']:<10}")
    print(f"{'Trivial (Most Common)':<30} | {triv_reply_res['bleu_mean']:<10} | {triv_reply_res['bleu_median']:<10}")
    
    print("\n### 3. Reply Quality (LLM-as-a-Judge, 1-5 Scale) ###")
    print(f"  Relevance   : {avg_relevance} / 5.0")
    print(f"  Helpfulness : {avg_helpfulness} / 5.0")
    print(f"  Tone        : {avg_tone} / 5.0")
    print(f"  Overall     : {avg_overall} / 5.0")
    
    print("\n### 4. Human Escalation Routing ###")
    print(f"{'System':<30} | {'Precision':<10} | {'Recall':<10} | {'F1':<10}")
    print("-" * 65)
    print(f"{'Main Agent (Hybrid)':<30} | {main_esc_res['precision']:<10} | {main_esc_res['recall']:<10} | {main_esc_res['f1']:<10}")
    print(f"{'Simple (Keywords Only)':<30} | {key_esc_res['precision']:<10} | {key_esc_res['recall']:<10} | {key_esc_res['f1']:<10}")
    print(f"{'Trivial (Always Escalate)':<30} | {triv_esc_res['precision']:<10} | {triv_esc_res['recall']:<10} | {triv_esc_res['f1']:<10}")
    
    # 5. Export results
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / 'evaluation_results.json'
    
    summary = {
        'timestamp': datetime.now().isoformat(),
        'golden_set_size': len(golden_set),
        'intent_classification': {
            'main_agent': main_intent_res,
            'tfidf_baseline': tfidf_intent_res,
            'random_baseline': rand_intent_res
        },
        'reply_quality': {
            'main_agent': main_reply_res,
            'nearest_neighbor': nn_reply_res,
            'trivial': triv_reply_res,
            'llm_judge': {
                'relevance': avg_relevance,
                'helpfulness': avg_helpfulness,
                'tone': avg_tone,
                'overall': avg_overall
            }
        },
        'escalation': {
            'main_agent': main_esc_res,
            'keyword_baseline': key_esc_res,
            'trivial_baseline': triv_esc_res
        },
        'sample_judgments': judge_scored[:10]
    }
    
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
        
    print(f"\nAll detailed metrics and confusion matrices saved to: {out_path}")
    print("Done! ✅")


if __name__ == '__main__':
    run_harness()