import uuid
from typing import Optional, List, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.db.session import get_db
from backend.app.core.security import get_current_user, require_officer, require_admin
from backend.app.models.entities import (
    InfrastructureAsset, AssetType, RiskLevel, User, UserRole, CivicIncident
)
from backend.app.schemas.common import ResponseBase, PaginatedResponse

router = APIRouter(prefix="/assets", tags=["Infrastructure Assets"])


# ==============================================================================
# SCHEMAS
# ==============================================================================

class AssetCreate(BaseModel):
    asset_code: str
    asset_type: AssetType
    name: str
    description: Optional[str] = None
    department_id: Optional[str] = None
    jurisdiction_id: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    health_score: Optional[float] = 100.0
    installation_date: Optional[datetime] = None
    notes: Optional[str] = None


class AssetHealthUpdate(BaseModel):
    health_score: float
    notes: Optional[str] = None
    ai_recommendation: Optional[str] = None


class AssetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    asset_code: str
    asset_type: AssetType
    name: str
    description: Optional[str] = None
    department_id: Optional[str] = None
    jurisdiction_id: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    health_score: float
    risk_score: float
    risk_level: RiskLevel
    complaint_count: int
    repair_count: int
    is_recurrent: bool
    last_repair_at: Optional[datetime] = None
    installation_date: Optional[datetime] = None
    ai_recommendation: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ==============================================================================
# ENDPOINTS
# ==============================================================================

@router.get("", response_model=ResponseBase[PaginatedResponse[AssetOut]])
async def list_assets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    asset_type: Optional[AssetType] = None,
    risk_level: Optional[RiskLevel] = None,
    department_id: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List infrastructure assets with optional filtering."""
    query = select(InfrastructureAsset).where(InfrastructureAsset.is_active == True)

    if asset_type:
        query = query.where(InfrastructureAsset.asset_type == asset_type)
    if risk_level:
        query = query.where(InfrastructureAsset.risk_level == risk_level)
    if department_id:
        query = query.where(InfrastructureAsset.department_id == department_id)
    if search:
        query = query.where(
            (InfrastructureAsset.name.ilike(f"%{search}%")) |
            (InfrastructureAsset.asset_code.ilike(f"%{search}%")) |
            (InfrastructureAsset.address.ilike(f"%{search}%"))
        )

    # Total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Pagination
    offset = (page - 1) * page_size
    items_query = query.order_by(InfrastructureAsset.health_score.asc()).offset(offset).limit(page_size)
    result = await db.execute(items_query)
    items = result.scalars().all()

    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return ResponseBase(
        data=PaginatedResponse(
            items=[AssetOut.model_validate(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    )


@router.get("/geojson")
async def get_assets_geojson(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return infrastructure assets as a GeoJSON FeatureCollection."""
    query = select(InfrastructureAsset).where(
        InfrastructureAsset.is_active == True,
        InfrastructureAsset.latitude.isnot(None),
        InfrastructureAsset.longitude.isnot(None)
    )
    result = await db.execute(query)
    assets = result.scalars().all()

    features = []
    for a in assets:
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [a.longitude, a.latitude]
            },
            "properties": {
                "id": a.id,
                "asset_code": a.asset_code,
                "name": a.name,
                "asset_type": a.asset_type.value,
                "health_score": a.health_score,
                "risk_level": a.risk_level.value,
                "complaint_count": a.complaint_count,
                "repair_count": a.repair_count
            }
        })

    return {
        "type": "FeatureCollection",
        "features": features
    }


@router.get("/{asset_id}", response_model=ResponseBase[AssetOut])
async def get_asset_detail(
    asset_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve detailed infrastructure asset record."""
    result = await db.execute(
        select(InfrastructureAsset).where(InfrastructureAsset.id == asset_id)
    )
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset {asset_id} not found"
        )

    return ResponseBase(data=AssetOut.model_validate(asset))


@router.post("", response_model=ResponseBase[AssetOut], status_code=status.HTTP_201_CREATED)
async def create_asset(
    payload: AssetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_officer),
):
    """Create a new infrastructure asset record (Officer/Admin)."""
    # Check duplicate asset code
    existing = await db.execute(
        select(InfrastructureAsset).where(InfrastructureAsset.asset_code == payload.asset_code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Asset code '{payload.asset_code}' already exists"
        )

    asset = InfrastructureAsset(
        asset_code=payload.asset_code,
        asset_type=payload.asset_type,
        name=payload.name,
        description=payload.description,
        department_id=payload.department_id,
        jurisdiction_id=payload.jurisdiction_id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        address=payload.address,
        health_score=payload.health_score or 100.0,
        risk_score=max(0.0, 100.0 - (payload.health_score or 100.0)),
        risk_level=RiskLevel.LOW if (payload.health_score or 100.0) >= 75 else RiskLevel.MEDIUM,
        installation_date=payload.installation_date,
        notes=payload.notes
    )
    db.add(asset)
    await db.commit()
    await db.refresh(asset)

    return ResponseBase(
        message="Asset registered successfully",
        data=AssetOut.model_validate(asset)
    )


@router.patch("/{asset_id}/health", response_model=ResponseBase[AssetOut])
async def update_asset_health(
    asset_id: str,
    payload: AssetHealthUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_officer),
):
    """Update asset health score and adjust risk metrics (Officer/Admin)."""
    result = await db.execute(
        select(InfrastructureAsset).where(InfrastructureAsset.id == asset_id)
    )
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset {asset_id} not found"
        )

    new_health = max(0.0, min(100.0, payload.health_score))
    risk_score = 100.0 - new_health

    if new_health >= 75.0:
        risk_lvl = RiskLevel.LOW
    elif new_health >= 50.0:
        risk_lvl = RiskLevel.MEDIUM
    elif new_health >= 25.0:
        risk_lvl = RiskLevel.HIGH
    else:
        risk_lvl = RiskLevel.CRITICAL

    asset.health_score = new_health
    asset.risk_score = risk_score
    asset.risk_level = risk_lvl
    if payload.notes:
        asset.notes = f"{asset.notes or ''}\n[{datetime.now(timezone.utc).strftime('%Y-%m-%d')}] {payload.notes}".strip()
    if payload.ai_recommendation:
        asset.ai_recommendation = payload.ai_recommendation

    await db.commit()
    await db.refresh(asset)

    return ResponseBase(
        message="Asset health updated successfully",
        data=AssetOut.model_validate(asset)
    )
