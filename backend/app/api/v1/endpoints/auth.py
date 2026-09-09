from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.app.db.session import get_db
from backend.app.models.entities import User, Citizen, Officer, Department, UserRole
from backend.app.schemas.auth import (
    CitizenRegisterRequest, OfficerRegisterRequest, LoginRequest,
    TokenResponse, RefreshTokenRequest, UserSummaryResponse, PasswordChangeRequest
)
from backend.app.schemas.common import ResponseBase
from backend.app.core.security import (
    get_password_hash, verify_password, create_access_token,
    create_refresh_token, decode_token, get_current_user, require_roles
)
from backend.app.core.config import settings
from backend.app.services.audit_service import audit_service

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register/citizen", response_model=ResponseBase[TokenResponse])
async def register_citizen(data: CitizenRegisterRequest, db: AsyncSession = Depends(get_db)):
    # Check if user already exists
    stmt = select(User).where(select(User.id).where(User.email == data.email.lower()).exists())
    existing = await db.scalar(stmt)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    user = User(
        email=data.email.lower(),
        hashed_password=get_password_hash(data.password),
        full_name=data.full_name,
        phone=data.phone,
        role=UserRole.CITIZEN,
        is_active=True,
        is_verified=True
    )
    db.add(user)
    await db.flush()

    citizen = Citizen(
        user_id=user.id,
        default_city=data.city
    )
    db.add(citizen)

    await audit_service.log_event(
        db=db,
        user_id=user.id,
        action="USER_REGISTERED",
        entity_name="User",
        entity_id=user.id,
        new_value={"role": UserRole.CITIZEN.value, "email": user.email}
    )

    await db.commit()

    access_token = create_access_token(user.id, user.role.value)
    refresh_token = create_refresh_token(user.id, user.role.value)

    user_summary = UserSummaryResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        role=user.role,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at,
        badge_score=citizen.badge_score
    )

    return ResponseBase(
        success=True,
        message="Registration successful",
        data=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_summary
        )
    )

@router.post("/register/officer", response_model=ResponseBase[TokenResponse])
async def register_officer(
    data: OfficerRegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(User).where(User.email == data.email.lower())
    res = await db.execute(stmt)
    if res.scalars().first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    user = User(
        email=data.email.lower(),
        hashed_password=get_password_hash(data.password),
        full_name=data.full_name,
        phone=data.phone,
        role=UserRole.OFFICER,
        is_active=True,
        is_verified=True
    )
    db.add(user)
    await db.flush()

    officer = Officer(
        user_id=user.id,
        department_id=data.department_id,
        jurisdiction_id=data.jurisdiction_id,
        badge_number=data.badge_number,
        designation=data.designation
    )
    db.add(officer)

    await audit_service.log_event(
        db=db,
        user_id=user.id,
        action="OFFICER_REGISTERED",
        entity_name="Officer",
        entity_id=officer.id,
        new_value={"badge_number": data.badge_number, "dept": data.department_id}
    )

    await db.commit()

    access_token = create_access_token(user.id, user.role.value)
    refresh_token = create_refresh_token(user.id, user.role.value)

    dept_stmt = select(Department.name).where(Department.id == data.department_id)
    dept_res = await db.execute(dept_stmt)
    dept_name = dept_res.scalar()

    user_summary = UserSummaryResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        role=user.role,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at,
        department_id=data.department_id,
        department_name=dept_name,
        badge_number=data.badge_number,
        designation=data.designation
    )

    return ResponseBase(
        success=True,
        message="Officer registered successfully",
        data=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_summary
        )
    )

@router.post("/login", response_model=ResponseBase[TokenResponse])
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(User)
        .options(
            selectinload(User.citizen_profile),
            selectinload(User.officer_profile).selectinload(Officer.department)
        )
        .where(User.email == data.email.lower())
    )
    res = await db.execute(stmt)
    user = res.scalars().first()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Account is disabled")

    access_token = create_access_token(user.id, user.role.value)
    refresh_token = create_refresh_token(user.id, user.role.value)

    user_summary = UserSummaryResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        role=user.role,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at,
        badge_score=user.citizen_profile.badge_score if user.citizen_profile else None,
        department_id=user.officer_profile.department_id if user.officer_profile else None,
        department_name=user.officer_profile.department.name if user.officer_profile and user.officer_profile.department else None,
        badge_number=user.officer_profile.badge_number if user.officer_profile else None,
        designation=user.officer_profile.designation if user.officer_profile else None
    )

    return ResponseBase(
        success=True,
        message="Login successful",
        data=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_summary
        )
    )

@router.post("/refresh", response_model=ResponseBase[TokenResponse])
async def refresh_token(data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    payload = decode_token(data.refresh_token)
    user_id = payload.get("sub")
    token_type = payload.get("type")

    if not user_id or token_type != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    stmt = (
        select(User)
        .options(
            selectinload(User.citizen_profile),
            selectinload(User.officer_profile).selectinload(Officer.department)
        )
        .where(User.id == user_id)
    )
    res = await db.execute(stmt)
    user = res.scalars().first()

    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    new_access_token = create_access_token(user.id, user.role.value)
    new_refresh_token = create_refresh_token(user.id, user.role.value)

    user_summary = UserSummaryResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        role=user.role,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at,
        badge_score=user.citizen_profile.badge_score if user.citizen_profile else None,
        department_id=user.officer_profile.department_id if user.officer_profile else None,
        department_name=user.officer_profile.department.name if user.officer_profile and user.officer_profile.department else None,
        badge_number=user.officer_profile.badge_number if user.officer_profile else None,
        designation=user.officer_profile.designation if user.officer_profile else None
    )

    return ResponseBase(
        success=True,
        message="Token refreshed successfully",
        data=TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_summary
        )
    )

@router.get("/me", response_model=ResponseBase[UserSummaryResponse])
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(User)
        .options(
            selectinload(User.citizen_profile),
            selectinload(User.officer_profile).selectinload(Officer.department)
        )
        .where(User.id == current_user.id)
    )
    res = await db.execute(stmt)
    user = res.scalars().first()

    user_summary = UserSummaryResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        role=user.role,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at,
        badge_score=user.citizen_profile.badge_score if user.citizen_profile else None,
        department_id=user.officer_profile.department_id if user.officer_profile else None,
        department_name=user.officer_profile.department.name if user.officer_profile and user.officer_profile.department else None,
        badge_number=user.officer_profile.badge_number if user.officer_profile else None,
        designation=user.officer_profile.designation if user.officer_profile else None
    )
    return ResponseBase(success=True, data=user_summary)
