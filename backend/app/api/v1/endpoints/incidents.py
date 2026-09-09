"""
Incidents API — Stage 3: Civic Incident Management
Routes complaints → incidents, exposes incident lifecycle and GeoJSON.
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, ConfigDict

from backend.app.db.session import get_async_session
from backend.app.core.security import get_current_user, require_officer
from backend.app.models.entities import (
    CivicIncident, IncidentReport, IncidentStatusHistory, InfrastructureAsset,
    User, UserRole, IncidentStatus
)
from backend.app.services.incident_service import IncidentService
from backend.app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/incidents", tags=["Incidents"])


# ── Response schemas ──────────────────────────────────────────────────────────

class IncidentSummary(BaseModel):
    id: str
    incident_number: str
    title: str
    status: str
    severity: str
    priority: str
    civic_impact_score: float
    report_count: int
    duplicate_count: int
    recurrence_count: int
    centroid_lat: Optional[float]
    centroid_lng: Optional[float]
    ward: Optional[str]
    city: Optional[str]
    category_code: Optional[str]
    department_name: Optional[str]
    first_reported_at: str
    last_updated_at: str
    impact_breakdown: Optional[dict] = None
    priority_explanation: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class IncidentStatusUpdate(BaseModel):
    new_status: str
    reason: Optional[str] = None


class IncidentMergeRequest(BaseModel):
    source_incident_id: str
    reason: Optional[str] = "Manual merge by authority"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _serialize_incident(inc: CivicIncident) -> dict:
    return {
        "id": inc.id,
        "incident_number": inc.incident_number,
        "title": inc.title,
        "status": inc.status.value,
        "severity": inc.severity.value,
        "priority": inc.priority.value,
        "civic_impact_score": inc.civic_impact_score,
        "report_count": inc.report_count,
        "duplicate_count": inc.duplicate_count,
        "recurrence_count": inc.recurrence_count,
        "centroid_lat": inc.centroid_lat,
        "centroid_lng": inc.centroid_lng,
        "ward": inc.ward,
        "city": inc.city,
        "category_code": inc.category.code if inc.category else None,
        "department_name": inc.department.name if inc.department else None,
        "first_reported_at": inc.first_reported_at.isoformat() if inc.first_reported_at else None,
        "last_updated_at": inc.last_updated_at.isoformat() if inc.last_updated_at else None,
        "impact_breakdown": inc.impact_breakdown_json,
        "priority_explanation": inc.priority_explanation,
    }


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("", summary="List civic incidents (paginated, filterable)")
async def list_incidents(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status_filter: Optional[str] = Query(None, alias="status"),
    department_id: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    min_impact: Optional[float] = Query(None, ge=0, le=100),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_officer),
):
    incidents, total = await IncidentService.list_incidents(
        db=db,
        skip=skip,
        limit=limit,
        status_filter=status_filter,
        department_id=department_id,
        severity=severity,
        min_impact=min_impact,
    )
    return {
        "success": True,
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": [_serialize_incident(inc) for inc in incidents],
    }


@router.get("/geojson", summary="All open incidents as GeoJSON for map layer")
async def incidents_geojson(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_officer),
):
    return await IncidentService.get_incidents_geojson(db)


@router.get("/{incident_id}", summary="Get civic incident detail with all supporting reports")
async def get_incident(
    incident_id: str,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_officer),
):
    incident = await IncidentService.get_incident_by_id(db, incident_id)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    serialized = _serialize_incident(incident)

    # Include supporting reports
    reports = []
    for ir in (incident.incident_reports or []):
        reports.append({
            "id": ir.id,
            "complaint_id": ir.complaint_id,
            "is_canonical": ir.is_canonical,
            "similarity_score": ir.similarity_score,
            "linked_at": ir.linked_at.isoformat() if ir.linked_at else None,
        })
    serialized["supporting_reports"] = reports

    # Include status history
    history = []
    for h in sorted((incident.status_history or []), key=lambda x: x.created_at):
        history.append({
            "from": h.previous_status.value if h.previous_status else None,
            "to": h.new_status.value,
            "reason": h.reason,
            "at": h.created_at.isoformat(),
        })
    serialized["status_history"] = history

    return serialized


@router.patch("/{incident_id}/status", summary="Transition incident status (OFFICER+)")
async def update_incident_status(
    incident_id: str,
    body: IncidentStatusUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_officer),
):
    incident = await IncidentService.get_incident_by_id(db, incident_id)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    try:
        new_status = IncidentStatus(body.new_status)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status: {body.new_status}. Must be one of: {[s.value for s in IncidentStatus]}"
        )

    updated = await IncidentService.transition_status(
        db=db,
        incident=incident,
        new_status=new_status,
        changed_by_user_id=current_user.id,
        reason=body.reason,
    )
    await db.commit()
    return {"id": updated.id, "incident_number": updated.incident_number, "status": updated.status.value}


@router.get("/{incident_id}/reports", summary="All citizen reports for an incident")
async def get_incident_reports(
    incident_id: str,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_officer),
):
    incident = await IncidentService.get_incident_by_id(db, incident_id)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    reports = []
    for ir in (incident.incident_reports or []):
        reports.append({
            "id": ir.id,
            "complaint_id": ir.complaint_id,
            "is_canonical": ir.is_canonical,
            "similarity_score": ir.similarity_score,
            "linked_at": ir.linked_at.isoformat() if ir.linked_at else None,
        })
    return {"incident_number": incident.incident_number, "report_count": len(reports), "reports": reports}
