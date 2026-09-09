"""
Research Metrics Suite — Stage 9
Standardized statistical and machine learning evaluation metrics.
"""
from typing import List, Dict, Any, Tuple
import math


def calculate_classification_metrics(y_true: List[str], y_pred: List[str]) -> Dict[str, float]:
    """Computes exact accuracy, macro precision, macro recall, and macro F1."""
    if not y_true or len(y_true) != len(y_pred):
        return {"accuracy": 0.0, "precision": 0.0, "recall": 0.0, "macro_f1": 0.0}

    categories = list(set(y_true))
    correct = sum(1 for t, p in zip(y_true, y_pred) if t == p)
    accuracy = correct / len(y_true)

    precisions = []
    recalls = []
    f1s = []

    for cat in categories:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == cat and p == cat)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != cat and p == cat)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == cat and p != cat)

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

        precisions.append(prec)
        recalls.append(rec)
        f1s.append(f1)

    return {
        "accuracy": round(accuracy, 4),
        "macro_precision": round(sum(precisions) / len(precisions), 4) if precisions else 0.0,
        "macro_recall": round(sum(recalls) / len(recalls), 4) if recalls else 0.0,
        "macro_f1": round(sum(f1s) / len(f1s), 4) if f1s else 0.0
    }


def calculate_binary_metrics(tp: int, fp: int, fn: int, tn: int) -> Dict[str, float]:
    """Computes precision, recall, specificity, and F1."""
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0.0

    return {
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "specificity": round(specificity, 4),
        "f1": round(f1, 4)
    }


def calculate_ordinal_regression_metrics(y_true_numeric: List[float], y_pred_numeric: List[float]) -> Dict[str, float]:
    """Computes MAE, RMSE, and tolerance accuracy within 1 ordinal step."""
    if not y_true_numeric or len(y_true_numeric) != len(y_pred_numeric):
        return {"mae": 0.0, "rmse": 0.0, "within_one_step_accuracy": 0.0}

    n = len(y_true_numeric)
    abs_diffs = [abs(t - p) for t, p in zip(y_true_numeric, y_pred_numeric)]
    sq_diffs = [(t - p) ** 2 for t, p in zip(y_true_numeric, y_pred_numeric)]

    mae = sum(abs_diffs) / n
    rmse = math.sqrt(sum(sq_diffs) / n)
    within_one = sum(1 for d in abs_diffs if d <= 1.0) / n

    return {
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "within_one_step_accuracy": round(within_one, 4)
    }
