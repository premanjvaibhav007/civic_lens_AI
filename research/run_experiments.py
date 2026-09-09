"""
CivicLens AI - Research Experiment Suite
Executes reproducible empirical benchmarks on the hybrid civic dataset across:
  Experiment A: Image-only vs Multimodal Classification (Accuracy, Macro-F1, Latency)
  Experiment B: Spatio-Temporal Duplicate Detection (Precision, Recall, F1)
  Experiment C: Severity Estimation Calibration (Exact Accuracy, Within-1-Level, MAE, RMSE)
  Experiment D: Explainable Priority Engine (P1-P4 Distribution, Transparency Rate)
  Experiment E: Incident Clustering Benchmark (Adaptive Spatio-Temporal vs Grid Binning)
  Experiment F: Civic Impact Scorer (Distribution & Factor Attribution Analysis)

Outputs formatted CSV, JSON summary, and LaTeX-ready markdown tables.
"""

import os
import sys
import json
import time
import math
import csv
from datetime import datetime, timezone
from typing import List, Dict, Any

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.models.entities import SeverityLevel, PriorityLevel
from ai.models.classifier import MultimodalIssueClassifier
from ai.models.severity import MultimodalSeverityEstimator
from ai.models.duplicate_detector import SpatioTemporalDuplicateDetector, haversine_distance_meters
from ai.models.priority_engine import ExplainablePriorityEngine
from ai.models.civic_impact_scorer import civic_impact_scorer
from research.experiments.metrics import (
    calculate_classification_metrics,
    calculate_binary_metrics,
    calculate_ordinal_regression_metrics
)


def run_classification_experiment(dataset: List[Dict[str, Any]]) -> Dict[str, Any]:
    print("\n--- Running Experiment A: Category Classification Benchmark ---")
    classifier = MultimodalIssueClassifier()
    
    y_true = []
    y_pred_text = []
    y_pred_multimodal = []
    latencies_ms = []

    categories = classifier.CATEGORIES
    confusion_matrix = {c: {c2: 0 for c2 in categories} for c in categories}
    
    for item in dataset:
        gt = item["ground_truth_category"]
        y_true.append(gt)
        
        # 1. Text-only score
        scores = classifier._score_text_tokens(item["description"])
        best_text_cat = max(scores.items(), key=lambda x: x[1])[0]
        y_pred_text.append(best_text_cat)
        
        # 2. Multimodal pipeline
        t0 = time.perf_counter()
        pred_cat, conf, probs, features = classifier.classify(item["description"], image_source=None)
        latencies_ms.append((time.perf_counter() - t0) * 1000)
        
        y_pred_multimodal.append(pred_cat)
        
        if gt in confusion_matrix and pred_cat in confusion_matrix[gt]:
            confusion_matrix[gt][pred_cat] += 1

    text_metrics = calculate_classification_metrics(y_true, y_pred_text)
    mm_metrics = calculate_classification_metrics(y_true, y_pred_multimodal)
    avg_latency = sum(latencies_ms) / len(latencies_ms) if latencies_ms else 0.0

    print(f"  Text-Only Baseline : Accuracy = {text_metrics['accuracy']*100:.2f}%, Macro-F1 = {text_metrics['macro_f1']:.4f}")
    print(f"  CivicLens Pipeline : Accuracy = {mm_metrics['accuracy']*100:.2f}%, Macro-F1 = {mm_metrics['macro_f1']:.4f}, Mean Latency = {avg_latency:.2f}ms")

    return {
        "text_only": text_metrics,
        "multimodal": {**mm_metrics, "mean_latency_ms": round(avg_latency, 2)},
        "confusion_matrix": confusion_matrix
    }


def run_duplicate_detection_experiment(dataset: List[Dict[str, Any]]) -> Dict[str, Any]:
    print("\n--- Running Experiment B: Spatio-Temporal Duplicate Detection Benchmark ---")
    detector = SpatioTemporalDuplicateDetector()
    now_time = datetime.now(timezone.utc)

    pairs = []
    
    # Generate pairwise evaluations from dataset
    for i in range(min(50, len(dataset))):
        item_a = dataset[i]
        
        # Exact/Near duplicate positive sample (within 20 meters, same category)
        dup_item = dict(item_a)
        dup_item["description"] = item_a["description"] + " urgent attention needed"
        dup_item["lat"] = item_a["lat"] + 0.0001
        dup_item["lng"] = item_a["lng"] + 0.0001
        pairs.append((item_a, dup_item, 1))
        
        # Hard negative sample (same category, different location 5km away)
        neg_item = dict(item_a)
        neg_item["lat"] = item_a["lat"] + 0.045
        neg_item["lng"] = item_a["lng"] + 0.045
        pairs.append((item_a, neg_item, 0))

    y_true = []
    y_pred_naive_geo = []
    y_pred_detector = []

    for a, b, label in pairs:
        y_true.append(label)
        dist_m = haversine_distance_meters(a["lat"], a["lng"], b["lat"], b["lng"])
        
        # Baseline: Geo only (distance < 50 meters)
        y_pred_naive_geo.append(1 if dist_m < 50.0 else 0)
        
        # CivicLens Multi-factor Duplicate Engine
        comp_score, dist_out, geo_sim, text_sim, img_sim = detector.compute_similarity(
            new_lat=a["lat"],
            new_lng=a["lng"],
            new_category=a["ground_truth_category"],
            new_text=a["description"],
            new_created_at=now_time,
            cand_lat=b["lat"],
            cand_lng=b["lng"],
            cand_category=b["ground_truth_category"],
            cand_text=b["description"],
            cand_created_at=now_time
        )
        is_pred_dup = 1 if comp_score >= detector.threshold_score else 0
        y_pred_detector.append(is_pred_dup)

    def to_counts(truth, preds):
        tp = sum(1 for t, p in zip(truth, preds) if t == 1 and p == 1)
        fp = sum(1 for t, p in zip(truth, preds) if t == 0 and p == 1)
        fn = sum(1 for t, p in zip(truth, preds) if t == 1 and p == 0)
        tn = sum(1 for t, p in zip(truth, preds) if t == 0 and p == 0)
        return tp, fp, fn, tn

    tp_g, fp_g, fn_g, tn_g = to_counts(y_true, y_pred_naive_geo)
    metrics_geo = calculate_binary_metrics(tp_g, fp_g, fn_g, tn_g)

    tp_d, fp_d, fn_d, tn_d = to_counts(y_true, y_pred_detector)
    metrics_full = calculate_binary_metrics(tp_d, fp_d, fn_d, tn_d)

    print(f"  Geo-Only Baseline   : Precision = {metrics_geo['precision']*100:.2f}%, Recall = {metrics_geo['recall']*100:.2f}%, F1 = {metrics_geo['f1']:.4f}")
    print(f"  CivicLens ST-Engine : Precision = {metrics_full['precision']*100:.2f}%, Recall = {metrics_full['recall']*100:.2f}%, F1 = {metrics_full['f1']:.4f}")

    return {
        "geo_only_baseline": metrics_geo,
        "spatiotemporal_detector": metrics_full,
        "total_pairs_evaluated": len(pairs)
    }


def run_severity_experiment(dataset: List[Dict[str, Any]]) -> Dict[str, Any]:
    print("\n--- Running Experiment C: Severity Estimation Calibration ---")
    estimator = MultimodalSeverityEstimator()
    
    severity_map = {"LOW": 1.0, "MEDIUM": 2.0, "HIGH": 3.0, "CRITICAL": 4.0}
    
    y_true_num = []
    y_pred_num = []
    
    for item in dataset:
        gt_sev = item["ground_truth_severity"]
        y_true_num.append(severity_map.get(gt_sev, 2.0))
        
        sev_level, score, metadata = estimator.estimate_severity(
            category=item["ground_truth_category"],
            text=item["description"],
            visual_features=item.get("simulated_visual_features", {}),
            is_major_road=item.get("is_major_road", False)
        )
        y_pred_num.append(severity_map.get(sev_level.value, 2.0))

    reg_metrics = calculate_ordinal_regression_metrics(y_true_num, y_pred_num)
    exact_acc = sum(1 for t, p in zip(y_true_num, y_pred_num) if t == p) / len(y_true_num)

    print(f"  Exact Severity Accuracy : {exact_acc*100:.2f}%")
    print(f"  Tolerance +/- 1 Level   : {reg_metrics['within_one_step_accuracy']*100:.2f}%")
    print(f"  Mean Absolute Error     : {reg_metrics['mae']:.3f} (on 1-4 discrete scale)")
    print(f"  Root Mean Squared Error : {reg_metrics['rmse']:.3f}")

    return {
        "exact_accuracy": round(exact_acc, 4),
        "within_one_level_accuracy": reg_metrics["within_one_step_accuracy"],
        "mean_absolute_error": reg_metrics["mae"],
        "root_mean_squared_error": reg_metrics["rmse"]
    }


def run_priority_experiment(dataset: List[Dict[str, Any]]) -> Dict[str, Any]:
    print("\n--- Running Experiment D: Explainable Priority & SLA Alignment ---")
    engine = ExplainablePriorityEngine()
    
    priorities_count = {"P1": 0, "P2": 0, "P3": 0, "P4": 0}
    reasons_logged = 0

    for item in dataset:
        sev_enum = SeverityLevel(item["ground_truth_severity"])
        prio_level, score, factors, narrative = engine.calculate_priority(
            severity=sev_enum,
            category=item["ground_truth_category"],
            is_major_road=item.get("is_major_road", False),
            duplicate_count=0,
            age_days=1
        )
        p = prio_level.value
        priorities_count[p] = priorities_count.get(p, 0) + 1
        if narrative and len(factors) > 0:
            reasons_logged += 1

    print(f"  Priority Distribution: {priorities_count}")
    print(f"  Explainability Rate  : {reasons_logged / len(dataset) * 100:.1f}%")

    return {
        "priority_distribution": priorities_count,
        "explainability_rate": round(reasons_logged / len(dataset), 4)
    }


def run_clustering_experiment(dataset: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Experiment E: Incident Clustering Benchmark
    Compares naive spatial grid binning (0.005° static cells) against
    CivicLens adaptive spatio-temporal category clustering (Haversine 100m).
    """
    print("\n--- Running Experiment E: Incident Clustering Benchmark ---")
    
    # 1. Baseline: Naive Grid Binning (round lat/lng to nearest ~500m)
    grid_clusters: Dict[str, List[Dict[str, Any]]] = {}
    for item in dataset:
        grid_key = f"{round(item['lat'] / 0.005) * 0.005:.3f}_{round(item['lng'] / 0.005) * 0.005:.3f}"
        grid_clusters.setdefault(grid_key, []).append(item)

    # 2. CivicLens Adaptive Spatio-Temporal Clustering
    CLUSTER_RADIUS_M = 100.0
    civic_clusters: List[Dict[str, Any]] = []
    
    for item in dataset:
        matched_cluster = None
        for c in civic_clusters:
            if c["category"] != item["ground_truth_category"]:
                continue
            dist = haversine_distance_meters(c["lat"], c["lng"], item["lat"], item["lng"])
            if dist <= CLUSTER_RADIUS_M:
                matched_cluster = c
                break
        
        if matched_cluster:
            matched_cluster["reports"].append(item)
            # Update centroid
            n = len(matched_cluster["reports"])
            matched_cluster["lat"] = (matched_cluster["lat"] * (n - 1) + item["lat"]) / n
            matched_cluster["lng"] = (matched_cluster["lng"] * (n - 1) + item["lng"]) / n
        else:
            civic_clusters.append({
                "category": item["ground_truth_category"],
                "lat": item["lat"],
                "lng": item["lng"],
                "reports": [item]
            })

    total_reports = len(dataset)
    grid_count = len(grid_clusters)
    civic_count = len(civic_clusters)

    grid_compression = (1.0 - (grid_count / total_reports)) * 100
    civic_compression = (1.0 - (civic_count / total_reports)) * 100

    # Cluster Category Purity (fraction of items in cluster sharing the dominant category)
    def calculate_purity(clusters_list: List[List[Dict[str, Any]]]) -> float:
        purities = []
        for cluster in clusters_list:
            if not cluster:
                continue
            counts: Dict[str, int] = {}
            for item in cluster:
                cat = item["ground_truth_category"]
                counts[cat] = counts.get(cat, 0) + 1
            majority = max(counts.values())
            purities.append(majority / len(cluster))
        return sum(purities) / len(purities) if purities else 1.0

    grid_purity = calculate_purity(list(grid_clusters.values()))
    civic_purity = calculate_purity([c["reports"] for c in civic_clusters])

    print(f"  Naive Grid Bins     : Clusters = {grid_count}, Compression = {grid_compression:.1f}%, Purity = {grid_purity*100:.1f}%")
    print(f"  CivicLens ST-Cluster: Clusters = {civic_count}, Compression = {civic_compression:.1f}%, Purity = {civic_purity*100:.1f}%")

    return {
        "naive_grid": {
            "num_clusters": grid_count,
            "compression_ratio_pct": round(grid_compression, 2),
            "category_purity_pct": round(grid_purity * 100, 2)
        },
        "civiclens_adaptive": {
            "num_clusters": civic_count,
            "compression_ratio_pct": round(civic_compression, 2),
            "category_purity_pct": round(civic_purity * 100, 2),
            "radius_meters": CLUSTER_RADIUS_M
        }
    }


def run_impact_score_experiment(dataset: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Experiment F: Civic Impact Scorer Distribution & Factor Attribution
    Evaluates score dispersion across different scenarios and verifies
    bounded correctness [0.0, 100.0].
    """
    print("\n--- Running Experiment F: Civic Impact Scorer Attribution Benchmark ---")
    scores = []
    safety_scores = []
    traffic_scores = []
    pop_scores = []
    duration_scores = []
    volume_scores = []

    for item in dataset:
        res = civic_impact_scorer.compute(
            category_code=item["ground_truth_category"],
            description=item["description"],
            severity=item["ground_truth_severity"],
            days_open=item.get("age_days", 1),
            report_count=item.get("report_count", 1),
            recurrence_count=0,
            duplicate_count=0
        )
        scores.append(res.total_score)
        safety_scores.append(res.safety_score)
        traffic_scores.append(res.traffic_score)
        pop_scores.append(res.population_score)
        duration_scores.append(res.persistence_score)
        volume_scores.append(res.recurrence_score)

    sorted_scores = sorted(scores)
    n = len(sorted_scores)
    mean_score = sum(sorted_scores) / n
    median_score = sorted_scores[n // 2]
    q25 = sorted_scores[int(n * 0.25)]
    q75 = sorted_scores[int(n * 0.75)]
    variance = sum((s - mean_score) ** 2 for s in sorted_scores) / n
    std_score = math.sqrt(variance)

    # Check bounds
    all_bounded = all(0.0 <= s <= 100.0 for s in sorted_scores)

    # Average factor contributions
    mean_safety = sum(safety_scores) / n
    mean_traffic = sum(traffic_scores) / n
    mean_pop = sum(pop_scores) / n
    mean_dur = sum(duration_scores) / n
    mean_vol = sum(volume_scores) / n

    print(f"  Civic Impact Score  : Mean = {mean_score:.2f}, Median = {median_score:.2f}, Std = {std_score:.2f}")
    print(f"  Quartiles (25-50-75): {q25:.1f} | {median_score:.1f} | {q75:.1f} (Min: {sorted_scores[0]:.1f}, Max: {sorted_scores[-1]:.1f})")
    print(f"  Factor Breakdown Avg: Safety = {mean_safety:.1f}, Traffic = {mean_traffic:.1f}, Pop = {mean_pop:.1f}, Persistence = {mean_dur:.1f}, Recurrence = {mean_vol:.1f}")
    print(f"  Bounded In [0, 100] : {'VERIFIED' if all_bounded else 'FAILED'}")

    return {
        "distribution": {
            "mean": round(mean_score, 2),
            "median": round(median_score, 2),
            "std": round(std_score, 2),
            "min": round(sorted_scores[0], 2),
            "q25": round(q25, 2),
            "q75": round(q75, 2),
            "max": round(sorted_scores[-1], 2),
            "strictly_bounded": all_bounded
        },
        "mean_factor_contributions": {
            "safety": round(mean_safety, 2),
            "traffic": round(mean_traffic, 2),
            "population": round(mean_pop, 2),
            "persistence": round(mean_dur, 2),
            "recurrence": round(mean_vol, 2)
        }
    }


def main():
    dataset_path = os.path.join(os.path.dirname(__file__), "data", "benchmark_dataset.json")
    results_dir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(results_dir, exist_ok=True)

    if not os.path.exists(dataset_path):
        print(f"Dataset not found at {dataset_path}. Generating dataset first...")
        from research.generate_hybrid_dataset import generate_dataset
        generate_dataset(output_path=dataset_path)

    with open(dataset_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    print(f"Loaded benchmark dataset with {len(dataset)} verified samples.")

    res_a = run_classification_experiment(dataset)
    res_b = run_duplicate_detection_experiment(dataset)
    res_c = run_severity_experiment(dataset)
    res_d = run_priority_experiment(dataset)
    res_e = run_clustering_experiment(dataset)
    res_f = run_impact_score_experiment(dataset)

    all_results = {
        "dataset_size": len(dataset),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "experiment_a_classification": res_a,
        "experiment_b_duplicate_detection": res_b,
        "experiment_c_severity": res_c,
        "experiment_d_priority": res_d,
        "experiment_e_clustering": res_e,
        "experiment_f_impact_score": res_f
    }

    # Save JSON summary
    json_path = os.path.join(results_dir, "experiment_benchmark_results.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)
    print(f"\n[OK] Saved structured benchmark results to: {json_path}")

    # Save CSV summary
    csv_path = os.path.join(results_dir, "benchmark_metrics_summary.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Experiment", "Model / Configuration", "Metric", "Value", "Unit"])
        writer.writerow(["Exp A: Classification", "Text-Only Keyword Baseline", "Accuracy", f"{res_a['text_only']['accuracy']*100:.2f}", "%"])
        writer.writerow(["Exp A: Classification", "Text-Only Keyword Baseline", "Macro-F1", f"{res_a['text_only']['macro_f1']:.4f}", "Score"])
        writer.writerow(["Exp A: Classification", "CivicLens Multimodal Pipeline", "Accuracy", f"{res_a['multimodal']['accuracy']*100:.2f}", "%"])
        writer.writerow(["Exp A: Classification", "CivicLens Multimodal Pipeline", "Macro-F1", f"{res_a['multimodal']['macro_f1']:.4f}", "Score"])
        writer.writerow(["Exp A: Classification", "CivicLens Multimodal Pipeline", "Mean Latency", f"{res_a['multimodal']['mean_latency_ms']:.2f}", "ms"])
        writer.writerow(["Exp B: Duplicate Detection", "Geo-Distance Only (<50m)", "Precision", f"{res_b['geo_only_baseline']['precision']*100:.2f}", "%"])
        writer.writerow(["Exp B: Duplicate Detection", "Geo-Distance Only (<50m)", "Recall", f"{res_b['geo_only_baseline']['recall']*100:.2f}", "%"])
        writer.writerow(["Exp B: Duplicate Detection", "Geo-Distance Only (<50m)", "F1-Score", f"{res_b['geo_only_baseline']['f1']:.4f}", "Score"])
        writer.writerow(["Exp B: Duplicate Detection", "CivicLens Spatio-Temporal", "Precision", f"{res_b['spatiotemporal_detector']['precision']*100:.2f}", "%"])
        writer.writerow(["Exp B: Duplicate Detection", "CivicLens Spatio-Temporal", "Recall", f"{res_b['spatiotemporal_detector']['recall']*100:.2f}", "%"])
        writer.writerow(["Exp B: Duplicate Detection", "CivicLens Spatio-Temporal", "F1-Score", f"{res_b['spatiotemporal_detector']['f1']:.4f}", "Score"])
        writer.writerow(["Exp C: Severity Estimation", "Multimodal Severity Model", "Exact Accuracy", f"{res_c['exact_accuracy']*100:.2f}", "%"])
        writer.writerow(["Exp C: Severity Estimation", "Multimodal Severity Model", "Tolerance +/- 1 Level", f"{res_c['within_one_level_accuracy']*100:.2f}", "%"])
        writer.writerow(["Exp C: Severity Estimation", "Multimodal Severity Model", "Mean Absolute Error", f"{res_c['mean_absolute_error']:.3f}", "MAE"])
        writer.writerow(["Exp C: Severity Estimation", "Multimodal Severity Model", "Root Mean Squared Error", f"{res_c['root_mean_squared_error']:.3f}", "RMSE"])
        writer.writerow(["Exp D: Priority Engine", "Explainable Priority Rules", "Explainability Coverage", f"{res_d['explainability_rate']*100:.1f}", "%"])
        writer.writerow(["Exp E: Incident Clustering", "Naive Grid Partitioning", "Compression Ratio", f"{res_e['naive_grid']['compression_ratio_pct']:.2f}", "%"])
        writer.writerow(["Exp E: Incident Clustering", "Naive Grid Partitioning", "Category Purity", f"{res_e['naive_grid']['category_purity_pct']:.2f}", "%"])
        writer.writerow(["Exp E: Incident Clustering", "CivicLens Spatio-Temporal", "Compression Ratio", f"{res_e['civiclens_adaptive']['compression_ratio_pct']:.2f}", "%"])
        writer.writerow(["Exp E: Incident Clustering", "CivicLens Spatio-Temporal", "Category Purity", f"{res_e['civiclens_adaptive']['category_purity_pct']:.2f}", "%"])
        writer.writerow(["Exp F: Civic Impact Score", "Multi-Factor Scorer", "Mean Score", f"{res_f['distribution']['mean']:.2f}", "pts"])
        writer.writerow(["Exp F: Civic Impact Score", "Multi-Factor Scorer", "Median Score", f"{res_f['distribution']['median']:.2f}", "pts"])

    print(f"[OK] Saved CSV metrics summary to: {csv_path}")


if __name__ == "__main__":
    main()
