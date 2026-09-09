from typing import Tuple, List, Dict, Any
from backend.app.models.entities import SeverityLevel, PriorityLevel
from backend.app.core.config import settings

class ExplainablePriorityEngine:
    """
    Computes priority level (P1-P4) using a multi-factor formula:
    - Severity (35%)
    - Public Safety Risk (25%)
    - Traffic / Location Impact (15%)
    - Duplicate Reports Frequency (15%)
    - Persistence / Duration (10%)
    
    Produces transparent human-understandable explanation strings.
    """
    SEVERITY_VALUES = {
        SeverityLevel.CRITICAL: 1.0,
        SeverityLevel.HIGH: 0.75,
        SeverityLevel.MEDIUM: 0.50,
        SeverityLevel.LOW: 0.25
    }

    SAFETY_HAZARD_CATEGORIES = [
        "OPEN_MANHOLE", "WATER_LEAKAGE", "POTHOLE", "DRAINAGE", "STREETLIGHT"
    ]

    def __init__(self, model_version: str = "1.2.0"):
        self.model_name = "civiclens-priority-engine"
        self.model_version = model_version

    def calculate_priority(
        self,
        severity: SeverityLevel,
        category: str,
        is_major_road: bool = False,
        duplicate_count: int = 0,
        age_days: int = 0,
        custom_weights: Dict[str, float] = None
    ) -> Tuple[PriorityLevel, float, List[str], str]:
        """
        Returns: (PriorityLevel, score, contributing_factor_list, explanation_narrative)
        """
        weights = custom_weights or {
            "severity": settings.PRIORITY_WEIGHT_SEVERITY,
            "safety_risk": settings.PRIORITY_WEIGHT_SAFETY_RISK,
            "traffic_impact": settings.PRIORITY_WEIGHT_TRAFFIC_IMPACT,
            "duplicates": settings.PRIORITY_WEIGHT_DUPLICATES,
            "persistence": settings.PRIORITY_WEIGHT_PERSISTENCE
        }

        # 1. Severity factor
        sev_score = self.SEVERITY_VALUES.get(severity, 0.50)

        # 2. Public safety risk
        safety_score = 0.85 if category.upper() in self.SAFETY_HAZARD_CATEGORIES else 0.35

        # 3. Location / Traffic impact
        traffic_score = 0.90 if is_major_road else 0.30

        # 4. Duplicate reports frequency factor (0 duplicates -> 0.1, 5+ duplicates -> 1.0)
        dup_score = min(1.0, 0.10 + (duplicate_count * 0.20))

        # 5. Persistence factor (0 days -> 0.1, 10+ days -> 1.0)
        persist_score = min(1.0, 0.10 + (age_days * 0.10))

        # Calculate weighted composite score in [0.0, 1.0]
        composite_score = (
            weights["severity"] * sev_score +
            weights["safety_risk"] * safety_score +
            weights["traffic_impact"] * traffic_score +
            weights["duplicates"] * dup_score +
            weights["persistence"] * persist_score
        )

        # Map to P1 - P4
        reasons = []
        if composite_score >= 0.75:
            priority = PriorityLevel.P1
        elif composite_score >= 0.55:
            priority = PriorityLevel.P2
        elif composite_score >= 0.35:
            priority = PriorityLevel.P3
        else:
            priority = PriorityLevel.P4

        # Generate transparent human-understandable reason bullets
        if sev_score >= 0.75:
            reasons.append(f"Severity classified as {severity.value}")
        if safety_score >= 0.70:
            reasons.append(f"High public safety hazard for category '{category}'")
        if is_major_road:
            reasons.append("Located on a major arterial thoroughfare")
        if duplicate_count > 0:
            reasons.append(f"{duplicate_count} nearby citizen complaint(s) reported for the same issue")
        if age_days >= 3:
            reasons.append(f"Unresolved issue has persisted for {age_days} days")

        if not reasons:
            reasons.append("Standard priority based on category baseline")

        # Synthesize narrative
        narrative = f"Assigned {priority.value} priority: " + "; ".join(reasons) + "."

        return priority, round(composite_score, 4), reasons, narrative

priority_engine = ExplainablePriorityEngine()
