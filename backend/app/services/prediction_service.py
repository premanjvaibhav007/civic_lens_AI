"""
Prediction Service — Stage 8 Core Service Logic
Coordinates historical aggregation and calls RiskPredictor.
Honest, grounded predictive intelligence.
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from backend.app.models.entities import (
    CivicIncident, InfrastructureAsset, Category, Jurisdiction,
    IncidentPrediction, RiskLevel
)
from backend.app.core.config import settings
from ai.models.risk_predictor import risk_predictor, RiskPrediction

logger = logging.getLogger("civiclens.prediction_service")


class PredictionService:

    @staticmethod
    async def get_system_history_days(db: AsyncSession) -> int:
        """Returns the total calendar days between the earliest recorded incident and now."""
        stmt = select(func.min(CivicIncident.first_reported_at))
        res = await db.execute(stmt)
        oldest = res.scalar()
        if not oldest:
            return 0
        return max(0, (datetime.now(timezone.utc) - oldest).days)

    @classmethod
    async def check_data_readiness(cls, db: AsyncSession) -> Dict[str, Any]:
        """Evaluates whether sufficient history has accumulated for predictive forecasting."""
        days = await cls.get_system_history_days(db)
        min_required = settings.PREDICTION_MIN_HISTORY_DAYS
        ready = days >= min_required

        count_stmt = select(func.count(CivicIncident.id))
        count_res = await db.execute(count_stmt)
        total_incidents = count_res.scalar() or 0

        return {
            "has_sufficient_data": ready,
            "days_of_data": days,
            "minimum_required_days": min_required,
            "total_incidents": total_incidents,
            "message": (
                f"Sufficient history accumulated ({days} days). Risk forecasting is active."
                if ready
                else f"Insufficient historical data ({days}/{min_required} days required). Forecasts remain in warm-up state."
            )
        }

    @classmethod
    async def predict_for_asset(
        cls,
        db: AsyncSession,
        asset_id: str
    ) -> RiskPrediction:
        """Generates a predictive failure risk analysis for a specific infrastructure asset."""
        stmt = select(InfrastructureAsset).where(InfrastructureAsset.id == asset_id)
        res = await db.execute(stmt)
        asset = res.scalar_one_or_none()

        if not asset:
            return RiskPrediction(
                risk_score=0.0,
                risk_level="LOW",
                prediction_window_days=settings.PREDICTION_WINDOW_DAYS,
                contributing_factors=[],
                confidence=0.0,
                insufficient_data=True,
                insufficient_data_message="Asset not found."
            )

        history_days = await cls.get_system_history_days(db)
        days_since_repair = None
        if asset.last_repair_at:
            days_since_repair = max(0, (datetime.now(timezone.utc) - asset.last_repair_at).days)

        # Asset type mapped to category code
        cat_code = asset.asset_type.value if hasattr(asset.asset_type, "value") else str(asset.asset_type)

        prediction = risk_predictor.predict(
            category_code=cat_code,
            historical_incident_count=asset.complaint_count,
            history_days=history_days,
            days_since_last_repair=days_since_repair,
            repair_count=asset.repair_count,
            recurrence_count=asset.complaint_count if asset.is_recurrent else 0
        )
        return prediction


prediction_service = PredictionService()
