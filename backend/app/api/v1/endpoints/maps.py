"""
Maps API — Stage 5: Civic Intelligence Map Layers
Serves GeoJSON endpoints for incidents, hotspots, and infrastructure assets.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.app.db.session import get_async_session
from backend.app.core.security import get_current_user, require_officer
from backend.app.models.entities import (
    InfrastructureAsset, User
)
from backend.app.services.incident_service import IncidentService
from backend.app.services.hotspot_service import HotspotService

router = APIRouter(prefix="/maps", tags=["Maps"])


@router.get("/incidents/geojson", summary="Open civic incidents as GeoJSON point layer")
async def map_incidents_geojson(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_officer),
):
    """Returns a GeoJSON FeatureCollection of all open incidents for the authority map."""
    return await IncidentService.get_incidents_geojson(db)


@router.get("/hotspots/geojson", summary="Detected infrastructure hotspot zones as GeoJSON")
async def map_hotspots_geojson(
    radius_m: float = Query(500.0, ge=100, le=5000, description="Clustering radius in metres"),
    min_incidents: int = Query(3, ge=2, le=50, description="Minimum incidents to form a hotspot"),
    days_lookback: int = Query(90, ge=7, le=365),
    force_refresh: bool = Query(False),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_officer),
):
    """
    Detects geographic hotspots using DBSCAN-lite spatial clustering.
    Results are cached for 1 hour. Use force_refresh=true to bypass cache.
    """
    hotspots = await HotspotService.detect_hotspots(
        db=db,
        radius_m=radius_m,
        min_incidents=min_incidents,
        days_lookback=days_lookback,
        force_refresh=force_refresh,
    )
    geojson = HotspotService.hotspots_to_geojson(hotspots)
    geojson["metadata"] = {
        "hotspot_count": len(hotspots),
        "detection_radius_m": radius_m,
        "min_incidents": min_incidents,
        "days_lookback": days_lookback,
    }
    return geojson


@router.get("/assets/geojson", summary="Infrastructure assets as GeoJSON point layer")
async def map_assets_geojson(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_officer),
):
    """Returns all active infrastructure assets as a GeoJSON layer."""
    stmt = select(InfrastructureAsset).where(
        InfrastructureAsset.is_active == True,
        InfrastructureAsset.latitude.isnot(None),
        InfrastructureAsset.longitude.isnot(None),
    )
    result = await db.execute(stmt)
    assets = result.scalars().all()

    features = []
    for asset in assets:
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [asset.longitude, asset.latitude],
            },
            "properties": {
                "id": asset.id,
                "asset_code": asset.asset_code,
                "name": asset.name,
                "asset_type": asset.asset_type.value,
                "health_score": asset.health_score,
                "risk_score": asset.risk_score,
                "risk_level": asset.risk_level.value,
                "complaint_count": asset.complaint_count,
                "is_recurrent": asset.is_recurrent,
                "ai_recommendation": asset.ai_recommendation,
            },
        })
    return {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {"asset_count": len(features)},
    }
