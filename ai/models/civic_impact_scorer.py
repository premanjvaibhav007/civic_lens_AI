"""
Civic Impact Scorer — Stage 4 / Stage 5 AI Engine
Computes a 0-100 Civic Impact Score with an explainable breakdown across
5 independently weighted dimensions. Score components are honest — based
only on data available at analysis time.
"""
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional


SAFETY_KEYWORDS = {
    "open_manhole": 30,
    "missing_cover": 28,
    "live_wire": 27,
    "electrical_hazard": 27,
    "broken_railing": 22,
    "road_collapse": 25,
    "open_pit": 24,
    "school_nearby": 15,
    "hospital_nearby": 12,
    "playground_nearby": 10,
}

TRAFFIC_KEYWORDS = {
    "main_road": 18,
    "highway": 20,
    "arterial": 16,
    "intersection": 14,
    "bus_route": 12,
    "traffic_light": 10,
    "school_zone": 14,
    "market": 10,
}

POPULATION_PROXIMITY = {
    "school": 20,
    "hospital": 18,
    "market": 15,
    "residential": 12,
    "bus_stop": 10,
    "park": 8,
}

CATEGORY_SAFETY_BASE = {
    "OPEN_MANHOLE": 25,
    "WATER_LEAKAGE": 18,
    "POTHOLE": 15,
    "DAMAGED_ROAD": 12,
    "DRAINAGE": 14,
    "STREETLIGHT": 10,
    "GARBAGE": 8,
    "FOOTPATH": 9,
    "DAMAGED_SIGN": 11,
    "ILLEGAL_DUMPING": 7,
    "PUBLIC_FACILITY": 6,
    "OTHER": 5,
}


@dataclass
class CivicImpactBreakdown:
    safety_score: float = 0.0       # 0–30
    population_score: float = 0.0  # 0–25
    traffic_score: float = 0.0     # 0–20
    persistence_score: float = 0.0 # 0–15
    recurrence_score: float = 0.0  # 0–10
    total_score: float = 0.0        # 0–100
    factors: List[Dict] = field(default_factory=list)
    explanation: str = ""


class CivicImpactScorer:
    """
    Computes a Civic Impact Score (0–100) with per-component breakdown.
    All scores are derived from real complaint data — never fabricated.
    """
    MODEL_NAME = "civiclens-impact-scorer"
    MODEL_VERSION = "1.0.0"

    def compute(
        self,
        category_code: str,
        description: str,
        severity: str,
        days_open: int,
        report_count: int,
        recurrence_count: int,
        duplicate_count: int,
    ) -> CivicImpactBreakdown:
        """
        Args:
            category_code: Detected category (e.g. "POTHOLE", "OPEN_MANHOLE")
            description: User-supplied complaint text
            severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
            days_open: Days since first report (0 if brand new)
            report_count: Number of distinct citizen reports for same incident
            recurrence_count: How many times this location has had incidents in past
            duplicate_count: Count of duplicate reports merged into this incident
        """
        text = (description or "").lower()
        breakdown = CivicImpactBreakdown()
        factors = []

        # ── 1. SAFETY SCORE (0–30) ────────────────────────────────────────────
        safety = float(CATEGORY_SAFETY_BASE.get(category_code, 5))

        # Severity modifier
        severity_mult = {"LOW": 0.5, "MEDIUM": 0.75, "HIGH": 1.0, "CRITICAL": 1.25}.get(severity, 0.75)
        safety *= severity_mult

        # Keyword boosters
        for kw, boost in SAFETY_KEYWORDS.items():
            if kw.replace("_", " ") in text or kw in text:
                safety += boost * 0.3
                factors.append({"factor": kw.replace("_", " ").title(), "contribution": round(boost * 0.3, 1), "dimension": "safety"})

        safety = min(30.0, safety)
        breakdown.safety_score = round(safety, 1)
        factors.append({"factor": f"Category base ({category_code})", "contribution": round(safety, 1), "dimension": "safety"})

        # ── 2. POPULATION EXPOSURE (0–25) ────────────────────────────────────
        population = 8.0  # baseline — some people always affected
        for kw, base in POPULATION_PROXIMITY.items():
            if kw in text:
                population += base * 0.4
                factors.append({"factor": f"Near {kw}", "contribution": round(base * 0.4, 1), "dimension": "population"})

        # More reports = more witnesses = higher population exposure
        if report_count >= 5:
            population += 8.0
            factors.append({"factor": f"{report_count} citizen reports", "contribution": 8.0, "dimension": "population"})
        elif report_count >= 3:
            population += 5.0
            factors.append({"factor": f"{report_count} citizen reports", "contribution": 5.0, "dimension": "population"})
        elif report_count >= 2:
            population += 2.5

        population = min(25.0, population)
        breakdown.population_score = round(population, 1)

        # ── 3. TRAFFIC IMPACT (0–20) ──────────────────────────────────────────
        traffic = 5.0  # baseline
        for kw, score in TRAFFIC_KEYWORDS.items():
            if kw.replace("_", " ") in text or kw in text:
                traffic += score * 0.4
                factors.append({"factor": kw.replace("_", " ").title(), "contribution": round(score * 0.4, 1), "dimension": "traffic"})

        # Potholes and road damage inherently affect traffic
        if category_code in ("POTHOLE", "DAMAGED_ROAD", "DAMAGED_SIGN"):
            traffic += 5.0

        traffic = min(20.0, traffic)
        breakdown.traffic_score = round(traffic, 1)

        # ── 4. PERSISTENCE (0–15) ─────────────────────────────────────────────
        # Logarithmic growth — a week-old problem matters more than one day,
        # but the marginal increase slows after a month
        if days_open > 0:
            persistence = min(15.0, math.log1p(days_open) * 3.2)
        else:
            persistence = 0.0
        breakdown.persistence_score = round(persistence, 1)
        if days_open > 0:
            factors.append({"factor": f"Open for {days_open} days", "contribution": round(persistence, 1), "dimension": "persistence"})

        # ── 5. RECURRENCE (0–10) ─────────────────────────────────────────────
        recurrence = min(10.0, recurrence_count * 2.5 + duplicate_count * 0.5)
        breakdown.recurrence_score = round(recurrence, 1)
        if recurrence_count > 0:
            factors.append({"factor": f"Recurred {recurrence_count}x at this location", "contribution": round(recurrence, 1), "dimension": "recurrence"})
        if duplicate_count > 0:
            factors.append({"factor": f"{duplicate_count} duplicate reports", "contribution": round(duplicate_count * 0.5, 1), "dimension": "recurrence"})

        # ── TOTAL ─────────────────────────────────────────────────────────────
        total = safety + population + traffic + persistence + recurrence
        total = round(min(100.0, total), 1)
        breakdown.total_score = total
        breakdown.factors = sorted(factors, key=lambda x: x["contribution"], reverse=True)

        # ── EXPLANATION ───────────────────────────────────────────────────────
        parts = []
        if safety >= 20:
            parts.append("High safety risk")
        if traffic >= 14:
            parts.append("Major traffic corridor")
        if population >= 18:
            parts.append("High population exposure")
        if persistence >= 8:
            parts.append(f"Persistent for {days_open} days")
        if recurrence_count >= 2:
            parts.append(f"Recurring problem ({recurrence_count} prior incidents)")
        if report_count >= 3:
            parts.append(f"{report_count} supporting citizen reports")

        if total >= 80:
            level = "CRITICAL CIVIC IMPACT"
        elif total >= 60:
            level = "HIGH CIVIC IMPACT"
        elif total >= 40:
            level = "MODERATE CIVIC IMPACT"
        else:
            level = "LOW CIVIC IMPACT"

        breakdown.explanation = f"{level} ({total}/100). " + (". ".join(parts) if parts else "Standard civic infrastructure issue.")
        return breakdown


civic_impact_scorer = CivicImpactScorer()
