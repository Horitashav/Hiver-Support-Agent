"""
Automated Evaluation Metrics.
Computes Accuracy, Macro F1, BLEU overlap, and Escalation Precision/Recall.
"""

from collections import Counter
import numpy as np
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, confusion_matrix, classification_report


def evaluate_intent(predictions, ground_truth):
    """Calculates accuracy and macro-F1 for intent categorization."""
    acc = accuracy_score(ground_truth, predictions)
    # macro-F1 gives equal weight to all classes (even small ones)
    macro_f1 = f1_score(ground_truth, predictions, average='macro', zero_division=0)
    weighted_f1 = f1_score(ground_truth, predictions, average='weighted', zero_division=0)
    
    labels = sorted(list(set(ground_truth + predictions)))
    cm = confusion_matrix(ground_truth, predictions, labels=labels)
    
    return {
        'accuracy': round(float(acc), 4),
        'macro_f1': round(float(macro_f1), 4),
        'weighted_f1': round(float(weighted_f1), 4),
        'confusion_labels': labels,
        'confusion_matrix': cm.tolist()
    }


def evaluate_escalation(predictions, ground_truth):
    """Calculates precision and recall for human escalation decisions."""
    # Convert booleans to integers (True -> 1, False -> 0)
    preds = [1 if p else 0 for p in predictions]
    truth = [1 if t else 0 for t in ground_truth]
    
    prec = precision_score(truth, preds, zero_division=0)
    rec = recall_score(truth, preds, zero_division=0)
    f1 = f1_score(truth, preds, zero_division=0)
    acc = accuracy_score(truth, preds)
    
    return {
        'precision': round(float(prec), 4),
        'recall': round(float(rec), 4),
        'f1': round(float(f1), 4),
        'accuracy': round(float(acc), 4),
        'total_escalated': int(sum(preds)),
        'escalation_rate': round(float(sum(preds) / len(preds)), 4) if len(preds) > 0 else 0.0
    }


def compute_bleu(reference, hypothesis):
    """Computes basic word-level overlap (BLEU-1 with brevity penalty)."""
    ref_tokens = reference.lower().split()
    hyp_tokens = hypothesis.lower().split()
    
    if len(hyp_tokens) == 0:
        return 0.0
        
    ref_counts = Counter(ref_tokens)
    hyp_counts = Counter(hyp_tokens)
    
    # Count how many words in the hypothesis appear in the reference
    clipped_matches = sum(min(count, ref_counts[word]) for word, count in hyp_counts.items())
    precision = clipped_matches / len(hyp_tokens)
    
    # Penalty if generated sentence is too short
    brevity_penalty = min(1.0, len(hyp_tokens) / max(len(ref_tokens), 1))
    return round(brevity_penalty * precision, 4)


def evaluate_replies(generated_replies, reference_replies):
    """Computes mean BLEU score across all generated answers."""
    bleu_scores = [
        compute_bleu(ref, gen) 
        for gen, ref in zip(generated_replies, reference_replies)
    ]
    return {
        'bleu_mean': round(float(np.mean(bleu_scores)), 4),
        'bleu_median': round(float(np.median(bleu_scores)), 4)
    }