"""
Authority AI Copilot API — Stage 6 Intelligence Layer
Natural-language query interface grounded entirely on real DB data.
RBAC-enforced: OFFICER+ only. Never fabricates results. Never bypasses permissions.
"""
import logging
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

from backend.app.db.session import get_async_session
from backend.app.core.security import require_officer
from backend.app.models.entities import (
    CivicIncident, Complaint, Department, Officer, User,
    IncidentStatus, ComplaintStatus, SeverityLevel, PriorityLevel
)

logger = logging.getLogger("civiclens.copilot")
router = APIRouter(prefix="/copilot", tags=["AI Copilot"])


class CopilotQuery(BaseModel):
    query: str
    context: Optional[dict] = None  # Optional: current ward/department filter


class CopilotResponse(BaseModel):
    answer: str
    intent: str
    source_records: List[dict]
    data_caveat: Optional[str] = None
    query_time_ms: float


# ── Intent Classification (rule-based, no LLM hallucination risk) ─────────────

def _classify_intent(query: str) -> str:
    q = query.lower()
    if any(k in q for k in ["urgent", "critical", "unresolved", "open", "pending"]):
        return "urgent_incidents"
    if any(k in q for k in ["why", "reason", "cause", "not resolved", "overdue", "sla"]):
        return "sla_analysis"
    if any(k in q for k in ["recurring", "repeat", "again", "pattern", "hotspot"]):
        return "recurring_analysis"
    if any(k in q for k in ["rain", "flood", "drain", "monsoon", "weather"]):
        return "weather_category_analysis"
    if any(k in q for k in ["officer", "assigned", "performance", "department"]):
        return "officer_performance"
    if any(k in q for k in ["ward", "zone", "area", "locality"]):
        return "ward_analysis"
    if any(k in q for k in ["pothole", "road", "streetlight", "garbage", "drainage", "water"]):
        return "category_analysis"
    return "general_stats"


# ── Grounded Query Tools (each fetches from real DB) ─────────────────────────

async def _tool_urgent_incidents(db: AsyncSession, query: str, limit: int = 5) -> dict:
    stmt = (
        select(CivicIncident)
        .options(selectinload(CivicIncident.category), selectinload(CivicIncident.department))
        .where(CivicIncident.status.in_([IncidentStatus.OPEN, IncidentStatus.ASSIGNED]))
        .order_by(desc(CivicIncident.civic_impact_score))
        .limit(limit)
    )
    res = await db.execute(stmt)
    incidents = res.scalars().all()

    records = [
        {
            "incident_number": inc.incident_number,
            "title": inc.title,
            "severity": inc.severity.value,
            "priority": inc.priority.value,
            "civic_impact_score": inc.civic_impact_score,
            "status": inc.status.value,
            "report_count": inc.report_count,
            "ward": inc.ward,
            "days_open": (datetime.now(timezone.utc) - inc.first_reported_at).days if inc.first_reported_at else 0,
            "category": inc.category.code if inc.category else None,
        }
        for inc in incidents
    ]

    if not records:
        answer = "No open or assigned civic incidents found at this time."
    else:
        top = records[0]
        answer = (
            f"The {len(records)} most urgent open incidents are listed below, ordered by Civic Impact Score. "
            f"The highest-priority incident is '{top['title']}' "
            f"({top['incident_number']}, {top['priority']}, Impact: {top['civic_impact_score']}/100, "
            f"{top['days_open']} days open). "
            f"All records shown are sourced directly from the CivicLens database."
        )
    return {"answer": answer, "records": records}


async def _tool_sla_analysis(db: AsyncSession, query: str) -> dict:
    now = datetime.now(timezone.utc)
    stmt = (
        select(CivicIncident)
        .options(selectinload(CivicIncident.category))
        .where(
            CivicIncident.status.in_([IncidentStatus.OPEN, IncidentStatus.ASSIGNED, IncidentStatus.IN_PROGRESS]),
            CivicIncident.sla_deadline.isnot(None),
            CivicIncident.sla_deadline < now,
        )
        .order_by(CivicIncident.sla_deadline)
        .limit(10)
    )
    res = await db.execute(stmt)
    incidents = res.scalars().all()

    records = [
        {
            "incident_number": inc.incident_number,
            "title": inc.title,
            "status": inc.status.value,
            "sla_deadline": inc.sla_deadline.isoformat() if inc.sla_deadline else None,
            "days_overdue": (now - inc.sla_deadline).days if inc.sla_deadline else 0,
            "ward": inc.ward,
        }
        for inc in incidents
    ]

    if not records:
        answer = "No SLA-breached incidents found. All incidents are within their resolution deadlines."
    else:
        answer = (
            f"{len(records)} incident(s) have breached their SLA deadline. "
            f"Oldest overdue: '{records[0]['incident_number']}' — {records[0]['days_overdue']} days past deadline. "
            f"Immediate escalation recommended."
        )
    return {"answer": answer, "records": records}


async def _tool_recurring_analysis(db: AsyncSession, query: str) -> dict:
    stmt = (
        select(CivicIncident)
        .options(selectinload(CivicIncident.category))
        .where(CivicIncident.recurrence_count >= 2)
        .order_by(desc(CivicIncident.recurrence_count))
        .limit(10)
    )
    res = await db.execute(stmt)
    incidents = res.scalars().all()

    records = [
        {
            "incident_number": inc.incident_number,
            "title": inc.title,
            "category": inc.category.code if inc.category else None,
            "recurrence_count": inc.recurrence_count,
            "report_count": inc.report_count,
            "ward": inc.ward,
            "civic_impact_score": inc.civic_impact_score,
        }
        for inc in incidents
    ]

    if not records:
        answer = "No recurring infrastructure incidents detected in the current dataset."
    else:
        answer = (
            f"{len(records)} location(s) show recurring infrastructure failures. "
            f"Most recurrent: '{records[0]['title']}' — {records[0]['recurrence_count']} recurrences. "
            f"These locations may indicate underlying infrastructure issues worth investigating."
        )
    return {"answer": answer, "records": records}


async def _tool_category_analysis(db: AsyncSession, query: str) -> dict:
    stmt = (
        select(
            CivicIncident.category_id,
            func.count(CivicIncident.id).label("count"),
            func.avg(CivicIncident.civic_impact_score).label("avg_impact"),
        )
        .where(CivicIncident.status != IncidentStatus.CLOSED)
        .group_by(CivicIncident.category_id)
        .order_by(desc("count"))
        .limit(10)
    )
    res = await db.execute(stmt)
    rows = res.all()

    # Get category names
    from backend.app.models.entities import Category
    cat_stmt = select(Category)
    cat_res = await db.execute(cat_stmt)
    cats = {c.id: c.code for c in cat_res.scalars().all()}

    records = [
        {
            "category": cats.get(row.category_id, "UNKNOWN"),
            "active_incident_count": row.count,
            "avg_civic_impact": round(row.avg_impact or 0, 1),
        }
        for row in rows
    ]
    answer = (
        f"Category breakdown of active incidents: "
        + ", ".join(f"{r['category']}: {r['active_incident_count']}" for r in records[:5])
        + ". Data sourced from live CivicLens incident database."
    ) if records else "No active incident category data available."
    return {"answer": answer, "records": records}


async def _tool_general_stats(db: AsyncSession, query: str) -> dict:
    total_res = await db.execute(select(func.count(CivicIncident.id)))
    total = total_res.scalar() or 0

    open_res = await db.execute(
        select(func.count(CivicIncident.id)).where(
            CivicIncident.status.in_([IncidentStatus.OPEN, IncidentStatus.ASSIGNED])
        )
    )
    open_count = open_res.scalar() or 0

    resolved_res = await db.execute(
        select(func.count(CivicIncident.id)).where(CivicIncident.status == IncidentStatus.RESOLVED)
    )
    resolved_count = resolved_res.scalar() or 0

    records = [
        {"metric": "Total Incidents", "value": total},
        {"metric": "Open / Assigned", "value": open_count},
        {"metric": "Resolved", "value": resolved_count},
        {"metric": "Resolution Rate", "value": f"{round(resolved_count/total*100, 1) if total else 0}%"},
    ]
    answer = (
        f"CivicLens currently tracks {total} civic incidents. "
        f"{open_count} are open or assigned, {resolved_count} are resolved "
        f"(resolution rate: {round(resolved_count/total*100, 1) if total else 0}%). "
        f"All figures from live database."
    )
    return {"answer": answer, "records": records}


TOOL_MAP = {
    "urgent_incidents": _tool_urgent_incidents,
    "sla_analysis": _tool_sla_analysis,
    "recurring_analysis": _tool_recurring_analysis,
    "weather_category_analysis": _tool_category_analysis,
    "category_analysis": _tool_category_analysis,
    "officer_performance": _tool_general_stats,
    "ward_analysis": _tool_general_stats,
    "general_stats": _tool_general_stats,
}


@router.post("/query", response_model=CopilotResponse, summary="Ask the AI Authority Copilot a question")
async def copilot_query(
    body: CopilotQuery,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_officer),
):
    """
    AI Authority Copilot: intent → DB tool → grounded answer.
    - All answers are based on real CivicLens database records.
    - RBAC enforced: OFFICER+ only.
    - Never fabricates or hallucinates data.
    - Source records are always included in the response.
    """
    import time
    start = time.time()

    if not body.query or len(body.query.strip()) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query must be at least 3 characters."
        )

    intent = _classify_intent(body.query)
    logger.info(f"[Copilot] Officer {current_user.email} | intent={intent} | query='{body.query[:80]}'")

    tool_fn = TOOL_MAP.get(intent, _tool_general_stats)
    try:
        result = await tool_fn(db, body.query)
    except Exception as e:
        logger.error(f"[Copilot] Tool error for intent '{intent}': {e}", exc_info=True)
        result = {
            "answer": "I encountered an error while querying the database. Please try again.",
            "records": [],
        }

    elapsed_ms = round((time.time() - start) * 1000, 1)
    return CopilotResponse(
        answer=result["answer"],
        intent=intent,
        source_records=result.get("records", []),
        data_caveat=(
            "All data shown is sourced directly from the CivicLens database. "
            "No information is generated or fabricated by the AI. "
            "Verify critical decisions with on-ground inspection."
        ),
        query_time_ms=elapsed_ms,
    )
