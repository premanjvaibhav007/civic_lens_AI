import re
from typing import Dict, Any, Tuple
from backend.app.models.entities import SeverityLevel

class MultimodalSeverityEstimator:
    """
    Estimates complaint severity (LOW, MEDIUM, HIGH, CRITICAL)
    using visual features, descriptive context, and category danger baselines.
    """
    CRITICAL_KEYWORDS = [
        "accident", "critical", "danger", "emergency", "fatal", "sparking", 
        "open manhole", "deep pit", "collapsed", "live wire", "burst pipe", 
        "flooding", "paralyzed", "fire hazard", "hospital route"
    ]
    
    HIGH_KEYWORDS = [
        "deep", "severe", "major", "blocked", "overflowing", "traffic jam", 
        "school zone", "main road", "highway", "broken cover", "unsafe", "dark road"
    ]
    
    LOW_KEYWORDS = [
        "minor", "small", "slight", "cosmetic", "paint", "side lane", "scratched", "faint"
    ]

    CATEGORY_BASELINE_SEVERITY = {
        "OPEN_MANHOLE": 0.85,    # High innate safety hazard
        "WATER_LEAKAGE": 0.65,
        "POTHOLE": 0.60,
        "DRAINAGE": 0.60,
        "STREETLIGHT": 0.50,
        "DAMAGED_ROAD": 0.55,
        "GARBAGE": 0.45,
        "ILLEGAL_DUMPING": 0.50,
        "FOOTPATH": 0.40,
        "DAMAGED_SIGN": 0.35,
        "PUBLIC_FACILITY": 0.35
    }

    def __init__(self, model_version: str = "1.2.0"):
        self.model_name = "civiclens-severity-estimator"
        self.model_version = model_version

    def estimate_severity(
        self,
        category: str,
        text: str,
        visual_features: Dict[str, Any],
        is_major_road: bool = False
    ) -> Tuple[SeverityLevel, float, Dict[str, Any]]:
        """
        Computes composite severity score in [0.0, 1.0] and maps to SeverityLevel.
        """
        text_lower = text.lower() if text else ""
        
        # 1. Baseline category severity (0.0 to 1.0)
        base_score = self.CATEGORY_BASELINE_SEVERITY.get(category.upper(), 0.50)

        # 2. Text keyword analysis
        text_modifier = 0.0
        matched_danger_keywords = []

        for kw in self.CRITICAL_KEYWORDS:
            if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
                text_modifier += 0.35
                matched_danger_keywords.append(kw)
                break

        for kw in self.HIGH_KEYWORDS:
            if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
                text_modifier += 0.20
                matched_danger_keywords.append(kw)
                break

        for kw in self.LOW_KEYWORDS:
            if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
                text_modifier -= 0.25
                break

        # 3. Visual disturbance modulation
        visual_modifier = 0.0
        if visual_features.get("valid"):
            edge_d = visual_features.get("edge_density", 0.0)
            var = visual_features.get("variance", 0.0)
            if edge_d > 0.12 or var > 0.06:
                visual_modifier += 0.15
            elif edge_d < 0.03:
                visual_modifier -= 0.10

        # 4. Location Context
        location_modifier = 0.15 if is_major_road else 0.0

        # Composite score
        composite_score = min(1.0, max(0.0, base_score + text_modifier + visual_modifier + location_modifier))

        # Classification thresholds
        if composite_score >= 0.80:
            severity = SeverityLevel.CRITICAL
        elif composite_score >= 0.60:
            severity = SeverityLevel.HIGH
        elif composite_score >= 0.35:
            severity = SeverityLevel.MEDIUM
        else:
            severity = SeverityLevel.LOW

        factors = {
            "baseline_score": round(base_score, 2),
            "text_modifier": round(text_modifier, 2),
            "visual_modifier": round(visual_modifier, 2),
            "location_modifier": round(location_modifier, 2),
            "composite_severity_score": round(composite_score, 2),
            "matched_danger_keywords": matched_danger_keywords
        }

        return severity, composite_score, factors

severity_estimator = MultimodalSeverityEstimator()
