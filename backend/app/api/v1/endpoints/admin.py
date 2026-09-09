from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, update
from sqlalchemy.orm import selectinload

from backend.app.db.session import get_db
from backend.app.models.entities import (
    Department, Jurisdiction, Category, RoutingRule, SLARule,
    AuditLog, User, Officer, Complaint, UserRole
)
from backend.app.schemas.admin import (
    DepartmentCreate, DepartmentResponse, JurisdictionCreate, JurisdictionResponse,
    CategoryCreate, CategoryResponse, RoutingRuleCreate, RoutingRuleResponse,
    SLARuleCreate, SLARuleResponse, AuditLogResponse
)
from backend.app.schemas.common import ResponseBase, PaginatedResponse
from backend.app.core.security import get_current_user, require_roles
from backend.app.services.audit_service import audit_service

router = APIRouter(prefix="/admin", tags=["Admin & System Configuration"])

# ----------------- DEPARTMENTS -----------------

@router.get("/departments", response_model=ResponseBase[List[DepartmentResponse]])
async def list_departments(
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Department)
        .options(
            selectinload(Department.officers),
            selectinload(Department.complaints)
        )
        .order_by(Department.name)
    )
    res = await db.execute(stmt)
    depts = res.scalars().all()

    items = []
    for d in depts:
        active_complaints = sum(1 for c in d.complaints if c.status not in ("RESOLVED", "REJECTED", "DUPLICATE"))
        items.append(DepartmentResponse(
            id=d.id,
            name=d.name,
            code=d.code,
            description=d.description,
            contact_email=d.contact_email,
            contact_phone=d.contact_phone,
            is_active=d.is_active,
            officer_count=len(d.officers),
            active_complaints_count=active_complaints,
            created_at=d.created_at
        ))
    return ResponseBase(success=True, data=items)

@router.post("/departments", response_model=ResponseBase[DepartmentResponse])
async def create_department(
    data: DepartmentCreate,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Department).where(Department.code == data.code.upper())
    res = await db.execute(stmt)
    if res.scalars().first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Department code already exists")

    dept = Department(
        name=data.name,
        code=data.code.upper(),
        description=data.description,
        contact_email=data.contact_email,
        contact_phone=data.contact_phone,
        is_active=True
    )
    db.add(dept)
    await audit_service.log_event(
        db=db,
        user_id=current_user.id,
        action="DEPARTMENT_CREATED",
        entity_name="Department",
        entity_id=dept.id,
        new_value={"name": data.name, "code": data.code}
    )
    await db.commit()
    await db.refresh(dept)

    return ResponseBase(
        success=True,
        message="Department created",
        data=DepartmentResponse(
            id=dept.id,
            name=dept.name,
            code=dept.code,
            description=dept.description,
            contact_email=dept.contact_email,
            contact_phone=dept.contact_phone,
            is_active=dept.is_active,
            officer_count=0,
            active_complaints_count=0,
            created_at=dept.created_at
        )
    )

# ----------------- JURISDICTIONS -----------------

@router.get("/jurisdictions", response_model=ResponseBase[List[JurisdictionResponse]])
async def list_jurisdictions(
    city: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Jurisdiction).where(Jurisdiction.is_active == True)
    if city:
        stmt = stmt.where(Jurisdiction.city.ilike(f"%{city}%"))
    stmt = stmt.order_by(Jurisdiction.city, Jurisdiction.zone, Jurisdiction.ward)
    res = await db.execute(stmt)
    jurisdictions = res.scalars().all()

    items = [
        JurisdictionResponse(
            id=j.id,
            city=j.city,
            zone=j.zone,
            ward=j.ward,
            boundary_geojson=j.boundary_geojson,
            is_active=j.is_active,
            created_at=j.created_at
        ) for j in jurisdictions
    ]
    return ResponseBase(success=True, data=items)

@router.post("/jurisdictions", response_model=ResponseBase[JurisdictionResponse])
async def create_jurisdiction(
    data: JurisdictionCreate,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    jur = Jurisdiction(
        city=data.city,
        zone=data.zone,
        ward=data.ward,
        boundary_geojson=data.boundary_geojson,
        is_active=True
    )
    db.add(jur)
    await audit_service.log_event(
        db=db,
        user_id=current_user.id,
        action="JURISDICTION_CREATED",
        entity_name="Jurisdiction",
        entity_id=jur.id,
        new_value={"city": data.city, "zone": data.zone, "ward": data.ward}
    )
    await db.commit()
    await db.refresh(jur)

    return ResponseBase(
        success=True,
        message="Jurisdiction created",
        data=JurisdictionResponse(
            id=jur.id,
            city=jur.city,
            zone=jur.zone,
            ward=jur.ward,
            boundary_geojson=jur.boundary_geojson,
            is_active=jur.is_active,
            created_at=jur.created_at
        )
    )

# ----------------- CATEGORIES -----------------

@router.get("/categories", response_model=ResponseBase[List[CategoryResponse]])
async def list_categories(
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Category)
        .options(selectinload(Category.default_department))
        .where(Category.is_active == True)
        .order_by(Category.name)
    )
    res = await db.execute(stmt)
    categories = res.scalars().all()

    items = [
        CategoryResponse(
            id=cat.id,
            name=cat.name,
            code=cat.code,
            description=cat.description,
            default_department_id=cat.default_department_id,
            default_department_name=cat.default_department.name if cat.default_department else None,
            default_priority=cat.default_priority,
            default_severity=cat.default_severity,
            icon_name=cat.icon_name,
            is_active=cat.is_active,
            created_at=cat.created_at
        ) for cat in categories
    ]
    return ResponseBase(success=True, data=items)

@router.post("/categories", response_model=ResponseBase[CategoryResponse])
async def create_category(
    data: CategoryCreate,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    cat = Category(
        name=data.name,
        code=data.code.upper(),
        description=data.description,
        default_department_id=data.default_department_id,
        default_priority=data.default_priority,
        default_severity=data.default_severity,
        icon_name=data.icon_name,
        is_active=True
    )
    db.add(cat)
    await audit_service.log_event(
        db=db,
        user_id=current_user.id,
        action="CATEGORY_CREATED",
        entity_name="Category",
        entity_id=cat.id,
        new_value={"name": data.name, "code": data.code}
    )
    await db.commit()
    await db.refresh(cat)

    dept_name = None
    if cat.default_department_id:
        d_res = await db.execute(select(Department.name).where(Department.id == cat.default_department_id))
        dept_name = d_res.scalar()

    return ResponseBase(
        success=True,
        message="Category created",
        data=CategoryResponse(
            id=cat.id,
            name=cat.name,
            code=cat.code,
            description=cat.description,
            default_department_id=cat.default_department_id,
            default_department_name=dept_name,
            default_priority=cat.default_priority,
            default_severity=cat.default_severity,
            icon_name=cat.icon_name,
            is_active=cat.is_active,
            created_at=cat.created_at
        )
    )

# ----------------- ROUTING RULES -----------------

@router.get("/routing-rules", response_model=ResponseBase[List[RoutingRuleResponse]])
async def list_routing_rules(
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.OFFICER)),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(RoutingRule, Category, Department, Jurisdiction)
        .outerjoin(Category, RoutingRule.category_id == Category.id)
        .join(Department, RoutingRule.target_department_id == Department.id)
        .outerjoin(Jurisdiction, RoutingRule.jurisdiction_id == Jurisdiction.id)
        .where(RoutingRule.is_active == True)
    )
    res = await db.execute(stmt)
    rows = res.all()

    items = []
    for rule, cat, dept, jur in rows:
        jur_info = f"{jur.city} ({jur.zone} - Ward {jur.ward})" if jur else "All Jurisdictions"
        items.append(RoutingRuleResponse(
            id=rule.id,
            name=rule.name,
            category_id=rule.category_id,
            category_name=cat.name if cat else "All Categories",
            jurisdiction_id=rule.jurisdiction_id,
            jurisdiction_info=jur_info,
            target_department_id=rule.target_department_id,
            target_department_name=dept.name,
            priority_boost=rule.priority_boost,
            is_active=rule.is_active,
            created_at=rule.created_at
        ))
    return ResponseBase(success=True, data=items)

@router.post("/routing-rules", response_model=ResponseBase[RoutingRuleResponse])
async def create_routing_rule(
    data: RoutingRuleCreate,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    rule = RoutingRule(
        name=data.name,
        category_id=data.category_id,
        jurisdiction_id=data.jurisdiction_id,
        target_department_id=data.target_department_id,
        priority_boost=data.priority_boost,
        is_active=True
    )
    db.add(rule)
    await audit_service.log_event(
        db=db,
        user_id=current_user.id,
        action="ROUTING_RULE_CREATED",
        entity_name="RoutingRule",
        entity_id=rule.id,
        new_value={"name": data.name, "dept": data.target_department_id}
    )
    await db.commit()
    await db.refresh(rule)

    dept_res = await db.execute(select(Department.name).where(Department.id == rule.target_department_id))
    dept_name = dept_res.scalar() or "Unknown Department"

    return ResponseBase(
        success=True,
        message="Routing rule created",
        data=RoutingRuleResponse(
            id=rule.id,
            name=rule.name,
            category_id=rule.category_id,
            category_name=None,
            jurisdiction_id=rule.jurisdiction_id,
            jurisdiction_info=None,
            target_department_id=rule.target_department_id,
            target_department_name=dept_name,
            priority_boost=rule.priority_boost,
            is_active=rule.is_active,
            created_at=rule.created_at
        )
    )

# ----------------- AUDIT LOGS -----------------

@router.get("/audit-logs", response_model=ResponseBase[PaginatedResponse[AuditLogResponse]])
async def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    action: Optional[str] = None,
    entity_name: Optional[str] = None,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(AuditLog, User.full_name)
        .outerjoin(User, AuditLog.user_id == User.id)
    )
    if action:
        query = query.where(AuditLog.action.ilike(f"%{action}%"))
    if entity_name:
        query = query.where(AuditLog.entity_name == entity_name)

    count_q = select(func.count()).select_from(query.subquery())
    total_count = (await db.execute(count_q)).scalar() or 0

    query = query.order_by(desc(AuditLog.created_at)).offset((page - 1) * page_size).limit(page_size)
    res = await db.execute(query)
    rows = res.all()

    items = [
        AuditLogResponse(
            id=log.id,
            user_id=log.user_id,
            user_name=full_name or "System",
            action=log.action,
            entity_name=log.entity_name,
            entity_id=log.entity_id,
            old_value_json=log.old_value_json,
            new_value_json=log.new_value_json,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            created_at=log.created_at
        ) for log, full_name in rows
    ]

    total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1

    return ResponseBase(
        success=True,
        data=PaginatedResponse(
            items=items,
            total=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    )
