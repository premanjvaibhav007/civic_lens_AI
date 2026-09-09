"""
Risk Predictor — Stage 8 Predictive Intelligence
Produces honest infrastructure risk predictions from historical complaint data.
NEVER fabricates predictions — returns INSUFFICIENT_DATA when history is sparse.
"""
import math
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from backend.app.core.config import settings


CATEGORY_SEASONALITY = {
    "DRAINAGE": [6, 7, 8, 9],      # Monsoon months
    "POTHOLE": [7, 8, 9, 10],      # Post-rain damage
    "WATER_LEAKAGE": [5, 6, 7],    # Summer heat expands pipes
    "STREETLIGHT": [11, 12, 1, 2], # Winter fog months
}

CATEGORY_BASE_RISK = {
    "OPEN_MANHOLE": 0.85,
    "WATER_LEAKAGE": 0.70,
    "POTHOLE": 0.65,
    "DRAINAGE": 0.60,
    "DAMAGED_ROAD": 0.55,
    "STREETLIGHT": 0.45,
    "FOOTPATH": 0.40,
    "GARBAGE": 0.35,
    "DAMAGED_SIGN": 0.38,
    "ILLEGAL_DUMPING": 0.32,
    "PUBLIC_FACILITY": 0.28,
    "OTHER": 0.25,
}


@dataclass
class RiskPrediction:
    risk_score: float                        # 0–100
    risk_level: str                          # LOW / MEDIUM / HIGH / CRITICAL
    prediction_window_days: int
    contributing_factors: List[Dict]
    confidence: float                        # 0–1
    model_name: str = "civiclens-risk-predictor"
    model_version: str = "1.0.0"
    insufficient_data: bool = False
    insufficient_data_message: str = ""


class InfrastructureRiskPredictor:
    """
    Heuristic rule-based risk predictor. Transparent about its limitations.
    Predictions are only generated when sufficient historical data exists.
    """
    MODEL_NAME = "civiclens-risk-predictor"
    MODEL_VERSION = "1.0.0"

    def predict(
        self,
        category_code: str,
        historical_incident_count: int,
        history_days: int,
        days_since_last_repair: Optional[int],
        repair_count: int,
        recurrence_count: int,
        current_month: Optional[int] = None,
    ) -> RiskPrediction:
        """
        Produce a risk prediction for a location/category combination.

        Returns INSUFFICIENT_DATA honestly when history_days < PREDICTION_MIN_HISTORY_DAYS.
        """
        if current_month is None:
            current_month = datetime.now(timezone.utc).month

        # ── INSUFFICIENT DATA GUARD ────────────────────────────────────────
        if history_days < settings.PREDICTION_MIN_HISTORY_DAYS:
            return RiskPrediction(
                risk_score=0.0,
                risk_level="LOW",
                prediction_window_days=settings.PREDICTION_WINDOW_DAYS,
                contributing_factors=[],
                confidence=0.0,
                model_name=self.MODEL_NAME,
                model_version=self.MODEL_VERSION,
                insufficient_data=True,
                insufficient_data_message=(
                    f"Insufficient historical data for reliable prediction. "
                    f"Need at least {settings.PREDICTION_MIN_HISTORY_DAYS} days of history "
                    f"(currently {history_days} days). Prediction will activate automatically "
                    f"once enough data accumulates."
                ),
            )

        factors: List[Dict] = []
        base = CATEGORY_BASE_RISK.get(category_code, 0.25)

        # ── 1. RECURRENCE FACTOR ──────────────────────────────────────────────
        if recurrence_count >= settings.PREDICTION_RECURRENCE_THRESHOLD:
            recurrence_boost = min(0.30, recurrence_count * 0.08)
            base = min(1.0, base + recurrence_boost)
            factors.append({
                "factor": f"Recurred {recurrence_count} times",
                "weight": round(recurrence_boost, 2),
                "impact": "HIGH",
            })

        # ── 2. INCIDENT FREQUENCY ─────────────────────────────────────────────
        if history_days > 0:
            incidents_per_month = (historical_incident_count / history_days) * 30
            if incidents_per_month > 2:
                freq_boost = min(0.25, incidents_per_month * 0.05)
                base = min(1.0, base + freq_boost)
                factors.append({
                    "factor": f"{incidents_per_month:.1f} incidents/month historically",
                    "weight": round(freq_boost, 2),
                    "impact": "HIGH" if freq_boost > 0.15 else "MEDIUM",
                })

        # ── 3. REPAIR AGE ─────────────────────────────────────────────────────
        if days_since_last_repair is not None:
            if days_since_last_repair > 90:
                repair_age_boost = min(0.20, (days_since_last_repair / 365) * 0.25)
                base = min(1.0, base + repair_age_boost)
                factors.append({
                    "factor": f"Last repaired {days_since_last_repair} days ago",
                    "weight": round(repair_age_boost, 2),
                    "impact": "MEDIUM",
                })
        elif repair_count == 0:
            factors.append({
                "factor": "No repair record found",
                "weight": 0.05,
                "impact": "LOW",
            })
            base = min(1.0, base + 0.05)

        # ── 4. SEASONALITY ────────────────────────────────────────────────────
        seasonal_months = CATEGORY_SEASONALITY.get(category_code, [])
        if current_month in seasonal_months:
            base = min(1.0, base + 0.15)
            factors.append({
                "factor": f"High-risk seasonal period for {category_code}",
                "weight": 0.15,
                "impact": "MEDIUM",
            })

        # ── RISK SCORE (0–100) ────────────────────────────────────────────────
        risk_score = round(base * 100, 1)

        if risk_score >= 75:
            risk_level = "CRITICAL"
        elif risk_score >= 55:
            risk_level = "HIGH"
        elif risk_score >= 35:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        # ── CONFIDENCE ────────────────────────────────────────────────────────
        # Confidence rises with more history, capped at 0.85 for heuristic model
        confidence = min(0.85, 0.40 + (history_days / 365) * 0.45)
        confidence = round(confidence, 2)

        return RiskPrediction(
            risk_score=risk_score,
            risk_level=risk_level,
            prediction_window_days=settings.PREDICTION_WINDOW_DAYS,
            contributing_factors=factors,
            confidence=confidence,
            model_name=self.MODEL_NAME,
            model_version=self.MODEL_VERSION,
        )


risk_predictor = InfrastructureRiskPredictor()
