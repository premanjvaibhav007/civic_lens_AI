"""
Predictions API — Stage 8: Predictive Infrastructure Intelligence
Honest predictions — only generated when sufficient data exists.
"""
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from backend.app.db.session import get_async_session
from backend.app.core.security import require_officer
from backend.app.models.entities import (
    CivicIncident, InfrastructureAsset, Category, Jurisdiction,
    User, IncidentStatus
)
from backend.app.core.config import settings
from ai.models.risk_predictor import risk_predictor

router = APIRouter(prefix="/predictions", tags=["Predictions"])


@router.get("/status", summary="Check if sufficient data exists for predictions")
async def prediction_data_status(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_officer),
):
    """
    Returns whether the system has accumulated enough historical data
    to generate reliable predictions. Always honest about data availability.
    """
    # Find earliest incident
    oldest_stmt = select(func.min(CivicIncident.first_reported_at))
    oldest_res = await db.execute(oldest_stmt)
    oldest_date = oldest_res.scalar()

    total_stmt = select(func.count(CivicIncident.id))
    total_res = await db.execute(total_stmt)
    total_incidents = total_res.scalar() or 0

    if oldest_date is None or total_incidents < 5:
        days_of_data = 0
    else:
        days_of_data = (datetime.now(timezone.utc) - oldest_date).days

    min_required = settings.PREDICTION_MIN_HISTORY_DAYS
    has_sufficient_data = days_of_data >= min_required

    return {
        "has_sufficient_data": has_sufficient_data,
        "days_of_data": days_of_data,
        "total_incidents": total_incidents,
        "minimum_required_days": min_required,
        "message": (
            f"Ready to generate predictions ({days_of_data} days of history)."
            if has_sufficient_data
            else (
                f"Insufficient historical data for reliable prediction. "
                f"Currently have {days_of_data} days of history. "
                f"Need at least {min_required} days. "
                f"Predictions will activate automatically once enough data accumulates."
            )
        ),
    }


@router.get("/areas", summary="Risk predictions by jurisdiction / ward")
async def predict_area_risks(
    jurisdiction_id: Optional[str] = Query(None),
    category_code: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_officer),
):
    """
    Generates infrastructure risk predictions per ward.
    Returns INSUFFICIENT_DATA for any ward lacking enough history.
    All predictions include confidence and contributing factors.
    """
    # Find earliest incident to compute history span
    oldest_stmt = select(func.min(CivicIncident.first_reported_at))
    oldest_res = await db.execute(oldest_stmt)
    oldest_date = oldest_res.scalar()
    history_days = (datetime.now(timezone.utc) - oldest_date).days if oldest_date else 0

    # If global data is insufficient, return early
    if history_days < settings.PREDICTION_MIN_HISTORY_DAYS:
        return {
            "status": "INSUFFICIENT_DATA",
            "message": (
                f"Insufficient historical data for reliable predictions. "
                f"Have {history_days} days, need {settings.PREDICTION_MIN_HISTORY_DAYS}."
            ),
            "predictions": [],
        }

    # Get categories to predict for
    if category_code:
        cat_stmt = select(Category).where(Category.code == category_code)
    else:
        cat_stmt = select(Category).where(Category.is_active == True)
    cat_res = await db.execute(cat_stmt)
    categories = cat_res.scalars().all()

    # Get jurisdictions
    if jurisdiction_id:
        jur_stmt = select(Jurisdiction).where(Jurisdiction.id == jurisdiction_id)
    else:
        jur_stmt = select(Jurisdiction).where(Jurisdiction.is_active == True)
    jur_res = await db.execute(jur_stmt)
    jurisdictions = jur_res.scalars().all()

    predictions = []
    cutoff_60d = datetime.now(timezone.utc) - timedelta(days=60)
    current_month = datetime.now(timezone.utc).month

    for jur in jurisdictions:
        for cat in categories:
            # Historical count for this jurisdiction+category
            inc_stmt = select(func.count(CivicIncident.id)).where(
                and_(
                    CivicIncident.jurisdiction_id == jur.id,
                    CivicIncident.category_id == cat.id,
                )
            )
            inc_res = await db.execute(inc_stmt)
            historical_count = inc_res.scalar() or 0

            if historical_count == 0:
                continue  # No data for this combo — skip

            # Recent incidents (60d)
            recent_stmt = select(func.count(CivicIncident.id)).where(
                and_(
                    CivicIncident.jurisdiction_id == jur.id,
                    CivicIncident.category_id == cat.id,
                    CivicIncident.first_reported_at >= cutoff_60d,
                )
            )
            recent_res = await db.execute(recent_stmt)
            recent_count = recent_res.scalar() or 0

            pred = risk_predictor.predict(
                category_code=cat.code,
                historical_incident_count=historical_count,
                history_days=history_days,
                days_since_last_repair=None,
                repair_count=0,
                recurrence_count=max(0, historical_count - 1),
                current_month=current_month,
            )

            if pred.insufficient_data:
                continue

            predictions.append({
                "jurisdiction_id": jur.id,
                "ward": jur.ward,
                "zone": jur.zone,
                "city": jur.city,
                "category": cat.code,
                "category_name": cat.name,
                "risk_score": pred.risk_score,
                "risk_level": pred.risk_level,
                "confidence": pred.confidence,
                "prediction_window_days": pred.prediction_window_days,
                "contributing_factors": pred.contributing_factors,
                "historical_count": historical_count,
                "recent_60d_count": recent_count,
                "model": f"{pred.model_name} v{pred.model_version}",
                "disclaimer": (
                    "This is a heuristic prediction, not a guarantee. "
                    "Confidence reflects data volume, not model accuracy. "
                    "Always combine with on-ground inspection."
                ),
            })

    predictions.sort(key=lambda p: p["risk_score"], reverse=True)
    return {
        "status": "OK",
        "prediction_count": len(predictions),
        "history_days": history_days,
        "predictions": predictions,
    }


@router.get("/assets/{asset_id}", summary="Risk prediction for a specific infrastructure asset")
async def predict_asset_risk(
    asset_id: str,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_officer),
):
    """
    Generates a risk prediction for a single infrastructure asset
    based on its complaint count, repair history, and recurrence.
    """
    asset_stmt = select(InfrastructureAsset).where(InfrastructureAsset.id == asset_id)
    asset_res = await db.execute(asset_stmt)
    asset = asset_res.scalars().first()
    if not asset:
        from fastapi import HTTPException, status as http_status
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Asset not found")

    oldest_stmt = select(func.min(CivicIncident.first_reported_at))
    oldest_res = await db.execute(oldest_stmt)
    oldest_date = oldest_res.scalar()
    history_days = (datetime.now(timezone.utc) - oldest_date).days if oldest_date else 0

    days_since_repair = None
    if asset.last_repair_at:
        days_since_repair = (datetime.now(timezone.utc) - asset.last_repair_at).days

    pred = risk_predictor.predict(
        category_code=asset.asset_type.value,
        historical_incident_count=asset.complaint_count,
        history_days=history_days,
        days_since_last_repair=days_since_repair,
        repair_count=asset.repair_count,
        recurrence_count=asset.complaint_count,
    )

    return {
        "asset_id": asset.id,
        "asset_code": asset.asset_code,
        "asset_name": asset.name,
        "asset_type": asset.asset_type.value,
        "current_health_score": asset.health_score,
        "current_risk_score": asset.risk_score,
        "prediction": {
            "insufficient_data": pred.insufficient_data,
            "message": pred.insufficient_data_message if pred.insufficient_data else None,
            "risk_score": pred.risk_score,
            "risk_level": pred.risk_level,
            "confidence": pred.confidence,
            "prediction_window_days": pred.prediction_window_days,
            "contributing_factors": pred.contributing_factors,
            "model": f"{pred.model_name} v{pred.model_version}",
        } if not pred.insufficient_data else {
            "insufficient_data": True,
            "message": pred.insufficient_data_message,
        },
        "disclaimer": (
            "Predictions are heuristic estimates based on historical patterns. "
            "They are decision support only — not authoritative risk assessments."
        ),
    }
