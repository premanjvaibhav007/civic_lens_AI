"""
Incident Service — Stage 3 Core Domain Logic
Manages clustering of citizen reports → CivicIncidents,
incident lifecycle transitions, and health score computation.
"""
import math
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc, update
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from backend.app.models.entities import (
    CivicIncident, IncidentReport, IncidentStatusHistory, InfrastructureAsset,
    Complaint, ComplaintLocation, ComplaintAIAnalysis, Category, Department,
    Jurisdiction, Officer, User,
    IncidentStatus, SeverityLevel, PriorityLevel, ComplaintStatus
)
from backend.app.core.config import settings

logger = logging.getLogger("civiclens.incident")


def _haversine_meters(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Compute great-circle distance in metres."""
    R = 6_371_000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


async def _generate_incident_number(db: AsyncSession) -> str:
    year = datetime.now(timezone.utc).year
    count_res = await db.execute(select(func.count(CivicIncident.id)))
    total = (count_res.scalar() or 0) + 1
    return f"INC-{year}-{total:05d}"


class IncidentService:

    # ──────────────────────────────────────────────────────────────────────────
    # 1. REPORT → INCIDENT CLUSTERING
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    async def find_nearby_open_incident(
        db: AsyncSession,
        lat: float,
        lng: float,
        category_code: str,
        radius_m: Optional[float] = None,
    ) -> Optional[CivicIncident]:
        """
        Search for an existing OPEN incident within radius_m metres that matches
        the same category. Returns the closest match or None.
        """
        radius_m = radius_m or settings.INCIDENT_CLUSTER_RADIUS_METERS
        cutoff_date = datetime.now(timezone.utc) - timedelta(
            days=settings.INCIDENT_CLUSTER_TIME_WINDOW_DAYS
        )
        stmt = (
            select(CivicIncident)
            .join(CivicIncident.category)
            .where(
                CivicIncident.status.in_([IncidentStatus.OPEN, IncidentStatus.ASSIGNED, IncidentStatus.IN_PROGRESS]),
                CivicIncident.centroid_lat.isnot(None),
                CivicIncident.centroid_lng.isnot(None),
                CivicIncident.first_reported_at >= cutoff_date,
            )
            .options(selectinload(CivicIncident.category))
        )
        result = await db.execute(stmt)
        candidates = result.scalars().all()

        best: Optional[CivicIncident] = None
        best_dist = float("inf")
        for inc in candidates:
            if inc.category and inc.category.code != category_code:
                continue
            dist = _haversine_meters(lat, lng, inc.centroid_lat, inc.centroid_lng)
            if dist <= radius_m and dist < best_dist:
                best_dist = dist
                best = inc
        return best

    @staticmethod
    async def create_incident_from_complaint(
        db: AsyncSession,
        complaint: Complaint,
        ai_analysis: Optional[ComplaintAIAnalysis],
        location: Optional[ComplaintLocation],
    ) -> CivicIncident:
        """
        Create a brand-new CivicIncident with this complaint as the canonical report.
        Called when no nearby incident exists.
        """
        number = await _generate_incident_number(db)
        severity = SeverityLevel.MEDIUM
        priority = PriorityLevel.P3
        if ai_analysis:
            severity = ai_analysis.predicted_severity
            priority = ai_analysis.predicted_priority

        incident = CivicIncident(
            incident_number=number,
            category_id=complaint.category_id,
            department_id=complaint.department_id,
            jurisdiction_id=complaint.jurisdiction_id,
            title=complaint.title,
            description=complaint.description,
            status=IncidentStatus.OPEN,
            severity=severity,
            priority=priority,
            centroid_lat=location.latitude if location else None,
            centroid_lng=location.longitude if location else None,
            ward=location.city if location else None,
            city=location.city if location else None,
            civic_impact_score=0.0,
            report_count=1,
            ai_confidence=ai_analysis.confidence if ai_analysis else 0.0,
            model_name=ai_analysis.model_name if ai_analysis else None,
            model_version=ai_analysis.model_version if ai_analysis else None,
            first_reported_at=complaint.created_at,
        )
        db.add(incident)
        await db.flush()  # get incident.id

        complaint.civic_incident_id = incident.id

        # Create canonical IncidentReport link
        link = IncidentReport(
            incident_id=incident.id,
            complaint_id=complaint.id,
            is_canonical=True,
            similarity_score=1.0,
        )
        db.add(link)

        # Create initial status history
        hist = IncidentStatusHistory(
            incident_id=incident.id,
            previous_status=None,
            new_status=IncidentStatus.OPEN,
            reason="Incident created from citizen report",
        )
        db.add(hist)
        await db.flush()

        logger.info(f"[IncidentService] Created new incident {number} from complaint {complaint.complaint_number}")
        return incident

    @staticmethod
    async def link_complaint_to_incident(
        db: AsyncSession,
        complaint: Complaint,
        incident: CivicIncident,
        similarity_score: float = 0.85,
    ) -> IncidentReport:
        """
        Link an existing complaint to an existing incident as a supporting report.
        Updates incident aggregated stats.
        """
        # Check not already linked
        existing_stmt = select(IncidentReport).where(
            and_(
                IncidentReport.incident_id == incident.id,
                IncidentReport.complaint_id == complaint.id,
            )
        )
        existing_res = await db.execute(existing_stmt)
        if existing_res.scalars().first():
            logger.debug(f"Complaint {complaint.id} already linked to incident {incident.id}")
            return None

        link = IncidentReport(
            incident_id=incident.id,
            complaint_id=complaint.id,
            is_canonical=False,
            similarity_score=similarity_score,
        )
        db.add(link)
        complaint.civic_incident_id = incident.id

        # Update aggregated stats
        await db.execute(
            update(CivicIncident)
            .where(CivicIncident.id == incident.id)
            .values(
                report_count=CivicIncident.report_count + 1,
                duplicate_count=CivicIncident.duplicate_count + 1,
                last_updated_at=datetime.now(timezone.utc),
            )
        )

        # Recompute centroid
        await IncidentService._recompute_centroid(db, incident.id)
        await db.flush()
        logger.info(f"[IncidentService] Linked complaint {complaint.complaint_number} to incident {incident.incident_number}")
        return link

    @staticmethod
    async def _recompute_centroid(db: AsyncSession, incident_id: str) -> None:
        """Recompute the geographic centroid from all linked complaints' locations."""
        stmt = (
            select(ComplaintLocation.latitude, ComplaintLocation.longitude)
            .join(IncidentReport, IncidentReport.complaint_id == ComplaintLocation.complaint_id)
            .where(IncidentReport.incident_id == incident_id)
        )
        result = await db.execute(stmt)
        coords = result.all()
        if not coords:
            return
        avg_lat = sum(r.latitude for r in coords) / len(coords)
        avg_lng = sum(r.longitude for r in coords) / len(coords)
        await db.execute(
            update(CivicIncident)
            .where(CivicIncident.id == incident_id)
            .values(centroid_lat=round(avg_lat, 6), centroid_lng=round(avg_lng, 6))
        )

    # ──────────────────────────────────────────────────────────────────────────
    # 2. UPDATE CIVIC IMPACT SCORE ON INCIDENT
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    async def update_civic_impact(
        db: AsyncSession,
        incident: CivicIncident,
        impact_score: float,
        impact_breakdown: Dict,
        explanation: str,
    ) -> None:
        await db.execute(
            update(CivicIncident)
            .where(CivicIncident.id == incident.id)
            .values(
                civic_impact_score=impact_score,
                impact_breakdown_json=impact_breakdown,
                priority_explanation=explanation,
                last_updated_at=datetime.now(timezone.utc),
            )
        )

    # ──────────────────────────────────────────────────────────────────────────
    # 3. STATUS TRANSITION
    # ──────────────────────────────────────────────────────────────────────────

    VALID_TRANSITIONS = {
        IncidentStatus.OPEN: [IncidentStatus.ASSIGNED, IncidentStatus.IN_PROGRESS, IncidentStatus.CLOSED],
        IncidentStatus.ASSIGNED: [IncidentStatus.IN_PROGRESS, IncidentStatus.OPEN, IncidentStatus.CLOSED],
        IncidentStatus.IN_PROGRESS: [IncidentStatus.RESOLVED, IncidentStatus.ASSIGNED, IncidentStatus.CLOSED],
        IncidentStatus.RESOLVED: [IncidentStatus.CLOSED, IncidentStatus.REOPENED],
        IncidentStatus.CLOSED: [IncidentStatus.REOPENED],
        IncidentStatus.REOPENED: [IncidentStatus.ASSIGNED, IncidentStatus.IN_PROGRESS],
    }

    @staticmethod
    async def transition_status(
        db: AsyncSession,
        incident: CivicIncident,
        new_status: IncidentStatus,
        changed_by_user_id: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> CivicIncident:
        allowed = IncidentService.VALID_TRANSITIONS.get(incident.status, [])
        if new_status not in allowed:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Cannot transition incident from {incident.status} to {new_status}. "
                       f"Allowed: {[s.value for s in allowed]}"
            )
        old_status = incident.status
        await db.execute(
            update(CivicIncident)
            .where(CivicIncident.id == incident.id)
            .values(
                status=new_status,
                last_updated_at=datetime.now(timezone.utc),
                resolved_at=datetime.now(timezone.utc) if new_status == IncidentStatus.RESOLVED else None,
            )
        )
        hist = IncidentStatusHistory(
            incident_id=incident.id,
            changed_by_user_id=changed_by_user_id,
            previous_status=old_status,
            new_status=new_status,
            reason=reason,
        )
        db.add(hist)
        await db.flush()
        incident.status = new_status
        return incident

    # ──────────────────────────────────────────────────────────────────────────
    # 4. QUERY HELPERS
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    async def get_incident_by_id(db: AsyncSession, incident_id: str) -> Optional[CivicIncident]:
        stmt = (
            select(CivicIncident)
            .options(
                selectinload(CivicIncident.category),
                selectinload(CivicIncident.department),
                selectinload(CivicIncident.jurisdiction),
                selectinload(CivicIncident.assigned_officer),
                selectinload(CivicIncident.incident_reports),
                selectinload(CivicIncident.status_history),
                selectinload(CivicIncident.predictions),
            )
            .where(CivicIncident.id == incident_id)
        )
        result = await db.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def list_incidents(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 50,
        status_filter: Optional[str] = None,
        department_id: Optional[str] = None,
        severity: Optional[str] = None,
        min_impact: Optional[float] = None,
    ) -> Tuple[List[CivicIncident], int]:
        base_stmt = select(CivicIncident).options(
            selectinload(CivicIncident.category),
            selectinload(CivicIncident.department),
        )
        count_stmt = select(func.count(CivicIncident.id))

        filters = []
        if status_filter:
            try:
                filters.append(CivicIncident.status == IncidentStatus(status_filter))
            except ValueError:
                pass
        if department_id:
            filters.append(CivicIncident.department_id == department_id)
        if severity:
            try:
                filters.append(CivicIncident.severity == SeverityLevel(severity))
            except ValueError:
                pass
        if min_impact is not None:
            filters.append(CivicIncident.civic_impact_score >= min_impact)

        if filters:
            base_stmt = base_stmt.where(and_(*filters))
            count_stmt = count_stmt.where(and_(*filters))

        total_res = await db.execute(count_stmt)
        total = total_res.scalar() or 0

        incidents_res = await db.execute(
            base_stmt.order_by(desc(CivicIncident.civic_impact_score))
            .offset(skip).limit(limit)
        )
        return incidents_res.scalars().all(), total

    @staticmethod
    async def get_incidents_geojson(db: AsyncSession) -> Dict:
        """Return all open incidents as GeoJSON FeatureCollection for the map."""
        stmt = (
            select(CivicIncident)
            .options(selectinload(CivicIncident.category))
            .where(
                CivicIncident.centroid_lat.isnot(None),
                CivicIncident.status.in_([IncidentStatus.OPEN, IncidentStatus.ASSIGNED, IncidentStatus.IN_PROGRESS]),
            )
        )
        result = await db.execute(stmt)
        incidents = result.scalars().all()

        features = []
        for inc in incidents:
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [inc.centroid_lng, inc.centroid_lat],
                },
                "properties": {
                    "id": inc.id,
                    "incident_number": inc.incident_number,
                    "title": inc.title,
                    "category": inc.category.code if inc.category else None,
                    "severity": inc.severity.value,
                    "priority": inc.priority.value,
                    "status": inc.status.value,
                    "civic_impact_score": inc.civic_impact_score,
                    "report_count": inc.report_count,
                    "city": inc.city,
                    "ward": inc.ward,
                },
            })
        return {"type": "FeatureCollection", "features": features}


incident_service = IncidentService()
