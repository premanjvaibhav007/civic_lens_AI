import base64
import asyncio
from typing import Optional, List
from fastapi import (
    APIRouter, Depends, HTTPException, status,
    UploadFile, File, Form, Query, BackgroundTasks
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_, and_
from sqlalchemy.orm import selectinload

from backend.app.db.session import get_db, AsyncSessionLocal
from backend.app.models.entities import (
    Complaint, ComplaintLocation, ComplaintImage, ComplaintAIAnalysis,
    ComplaintAssignment, ComplaintStatusHistory, ComplaintComment,
    ResolutionEvidence, DuplicateCandidate, Citizen, Department,
    Jurisdiction, Officer, User, Category,
    ComplaintStatus, SeverityLevel, PriorityLevel, UserRole
)
from backend.app.schemas.complaint import (
    ComplaintCreateRequest, ComplaintStatusUpdateRequest,
    ComplaintAssignmentRequest, ResolutionSubmissionRequest,
    CitizenVerificationRequest, CommentCreateRequest,
    ComplaintDetailResponse, ComplaintListItemResponse,
    LocationCreate, LocationResponse, ImageResponse, AIAnalysisResponse,
    DuplicateCandidateResponse, StatusHistoryResponse, CommentResponse,
    ResolutionEvidenceResponse
)
from backend.app.schemas.common import ResponseBase, PaginatedResponse
from backend.app.core.security import get_current_user, require_roles
from backend.app.services.complaint_service import complaint_service
from backend.app.services.storage_service import storage_service
from backend.app.services.ai_service import ai_service
from ai.models.duplicate_detector import haversine_distance_meters

router = APIRouter(prefix="/complaints", tags=["Complaints"])

async def _run_ai_pipeline_bg(complaint_id: str):
    """Background task to run AI analysis with its own DB session"""
    async with AsyncSessionLocal() as session:
        try:
            await ai_service.analyze_complaint(session, complaint_id)
        except Exception as e:
            print(f"Error in bg AI pipeline: {e}")

@router.post("", response_model=ResponseBase[ComplaintListItemResponse])
async def create_complaint(
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    description: Optional[str] = Form(None),
    category_id: Optional[str] = Form(None),
    latitude: float = Form(...),
    longitude: float = Form(...),
    accuracy_meters: float = Form(0.0),
    address: Optional[str] = Form(None),
    landmark: Optional[str] = Form(None),
    city: Optional[str] = Form(None),
    state: Optional[str] = Form(None),
    postal_code: Optional[str] = Form(None),
    is_manual_adjusted: bool = Form(False),
    image: Optional[UploadFile] = File(None),
    image_base64: Optional[str] = Form(None),
    submission_channel: str = Form("ANDROID_APP"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    image_url, thumb_url, file_size, mime_type, image_hash = None, None, 0, "image/jpeg", None

    # Handle image upload
    if image and image.filename:
        image_url, thumb_url, file_size, mime_type, image_hash = await storage_service.save_upload_file(image)
    elif image_base64:
        try:
            img_bytes = base64.b64decode(image_base64)
            image_url, thumb_url, file_size, mime_type, image_hash = storage_service.save_bytes_image(img_bytes)
        except Exception:
            pass

    req_data = ComplaintCreateRequest(
        title=title,
        description=description,
        category_id=category_id,
        location=LocationCreate(
            latitude=latitude,
            longitude=longitude,
            accuracy_meters=accuracy_meters,
            address=address,
            landmark=landmark,
            city=city,
            state=state,
            postal_code=postal_code,
            is_manual_adjusted=is_manual_adjusted
        ),
        submission_channel=submission_channel
    )

    complaint = await complaint_service.create_complaint(
        db=db,
        citizen_user_id=current_user.id,
        data=req_data,
        image_url=image_url,
        thumbnail_url=thumb_url,
        file_size_bytes=file_size,
        mime_type=mime_type,
        image_hash=image_hash
    )

    # Trigger asynchronous background AI triage
    background_tasks.add_task(_run_ai_pipeline_bg, complaint.id)

    response_item = ComplaintListItemResponse(
        id=complaint.id,
        complaint_number=complaint.complaint_number,
        title=complaint.title,
        status=complaint.status,
        priority=complaint.priority,
        severity=complaint.severity,
        primary_image_url=image_url,
        primary_thumbnail_url=thumb_url,
        latitude=latitude,
        longitude=longitude,
        address=address,
        city=city,
        is_duplicate=False,
        created_at=complaint.created_at,
        updated_at=complaint.updated_at
    )

    return ResponseBase(
        success=True,
        message="Complaint submitted successfully. AI analysis scheduled.",
        data=response_item
    )

@router.get("", response_model=ResponseBase[PaginatedResponse[ComplaintListItemResponse]])
async def list_complaints(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[ComplaintStatus] = None,
    priority: Optional[PriorityLevel] = None,
    category_id: Optional[str] = None,
    department_id: Optional[str] = None,
    search: Optional[str] = None,
    my_complaints_only: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(Complaint)
        .options(
            selectinload(Complaint.location),
            selectinload(Complaint.images),
            selectinload(Complaint.category),
            selectinload(Complaint.department),
            selectinload(Complaint.ai_analysis)
        )
    )

    # Role scoping
    if current_user.role == UserRole.CITIZEN:
        if my_complaints_only:
            cit_stmt = select(Citizen.id).where(Citizen.user_id == current_user.id)
            cit_res = await db.execute(cit_stmt)
            citizen_id = cit_res.scalar()
            query = query.where(Complaint.citizen_id == citizen_id)
    elif current_user.role == UserRole.OFFICER:
        # Officer sees assigned or department complaints
        off_stmt = select(Officer).where(Officer.user_id == current_user.id)
        off_res = await db.execute(off_stmt)
        officer = off_res.scalars().first()
        if officer and not my_complaints_only:
            query = query.where(
                or_(
                    Complaint.department_id == officer.department_id,
                    Complaint.assigned_officer_id == officer.id
                )
            )

    # Filter clauses
    if status:
        query = query.where(Complaint.status == status)
    if priority:
        query = query.where(Complaint.priority == priority)
    if category_id:
        query = query.where(Complaint.category_id == category_id)
    if department_id:
        query = query.where(Complaint.department_id == department_id)
    if search:
        search_fmt = f"%{search}%"
        query = query.where(
            or_(
                Complaint.title.ilike(search_fmt),
                Complaint.complaint_number.ilike(search_fmt),
                Complaint.description.ilike(search_fmt)
            )
        )

    # Total count
    count_query = select(func.count()).select_from(query.subquery())
    total_count = (await db.execute(count_query)).scalar() or 0

    # Pagination & sort by created_at desc
    query = query.order_by(desc(Complaint.created_at)).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    complaints = result.scalars().all()

    items = []
    for c in complaints:
        primary_img = next((img for img in c.images if img.is_primary), c.images[0] if c.images else None)
        items.append(ComplaintListItemResponse(
            id=c.id,
            complaint_number=c.complaint_number,
            title=c.title,
            category_name=c.category.name if c.category else None,
            department_name=c.department.name if c.department else None,
            status=c.status,
            priority=c.priority,
            severity=c.severity,
            primary_image_url=primary_img.image_url if primary_img else None,
            primary_thumbnail_url=primary_img.thumbnail_url if primary_img else None,
            latitude=c.location.latitude if c.location else None,
            longitude=c.location.longitude if c.location else None,
            address=c.location.address if c.location else None,
            city=c.location.city if c.location else None,
            is_duplicate=c.is_duplicate,
            ai_confidence=c.ai_analysis.confidence if c.ai_analysis else None,
            created_at=c.created_at,
            updated_at=c.updated_at
        ))

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

@router.get("/nearby", response_model=ResponseBase[List[ComplaintListItemResponse]])
async def get_nearby_complaints(
    latitude: float = Query(...),
    longitude: float = Query(...),
    radius_meters: float = Query(3000.0, ge=100.0, le=20000.0),
    category_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Public nearby complaints endpoint for map visualization.
    Excludes sensitive citizen personal information.
    """
    query = (
        select(Complaint)
        .options(
            selectinload(Complaint.location),
            selectinload(Complaint.images),
            selectinload(Complaint.category)
        )
        .where(
            Complaint.status.notin_([ComplaintStatus.DRAFT, ComplaintStatus.REJECTED])
        )
    )
    if category_id:
        query = query.where(Complaint.category_id == category_id)

    res = await db.execute(query)
    all_complaints = res.scalars().all()

    nearby_items = []
    for c in all_complaints:
        if not c.location:
            continue
        dist = haversine_distance_meters(latitude, longitude, c.location.latitude, c.location.longitude)
        if dist <= radius_meters:
            primary_img = next((img for img in c.images if img.is_primary), c.images[0] if c.images else None)
            nearby_items.append(ComplaintListItemResponse(
                id=c.id,
                complaint_number=c.complaint_number,
                title=c.title,
                category_name=c.category.name if c.category else None,
                status=c.status,
                priority=c.priority,
                severity=c.severity,
                primary_image_url=primary_img.image_url if primary_img else None,
                primary_thumbnail_url=primary_img.thumbnail_url if primary_img else None,
                latitude=c.location.latitude,
                longitude=c.location.longitude,
                address=c.location.address,
                city=c.location.city,
                is_duplicate=c.is_duplicate,
                created_at=c.created_at,
                updated_at=c.updated_at
            ))

    return ResponseBase(success=True, data=nearby_items)

@router.get("/{id}", response_model=ResponseBase[ComplaintDetailResponse])
async def get_complaint_detail(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Complaint)
        .options(
            selectinload(Complaint.citizen).selectinload(Citizen.user),
            selectinload(Complaint.category),
            selectinload(Complaint.department),
            selectinload(Complaint.jurisdiction),
            selectinload(Complaint.assigned_officer).selectinload(Officer.user),
            selectinload(Complaint.location),
            selectinload(Complaint.images),
            selectinload(Complaint.ai_analysis),
            selectinload(Complaint.status_history).selectinload(ComplaintStatusHistory.complaint),
            selectinload(Complaint.comments),
            selectinload(Complaint.resolution_evidence).selectinload(ResolutionEvidence.officer).selectinload(Officer.user),
            selectinload(Complaint.duplicate_candidates).selectinload(DuplicateCandidate.candidate).selectinload(Complaint.images)
        )
        .where(or_(Complaint.id == id, Complaint.complaint_number == id))
    )
    res = await db.execute(stmt)
    c = res.scalars().first()
    if not c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")

    # Map Location
    loc_resp = None
    if c.location:
        loc_resp = LocationResponse(
            id=c.location.id,
            latitude=c.location.latitude,
            longitude=c.location.longitude,
            accuracy_meters=c.location.accuracy_meters,
            address=c.location.address,
            landmark=c.location.landmark,
            city=c.location.city,
            state=c.location.state,
            postal_code=c.location.postal_code,
            is_manual_adjusted=c.location.is_manual_adjusted
        )

    # Map Images
    images_resp = [
        ImageResponse(
            id=img.id,
            image_url=img.image_url,
            thumbnail_url=img.thumbnail_url,
            file_size_bytes=img.file_size_bytes,
            mime_type=img.mime_type,
            is_primary=img.is_primary,
            captured_at=img.captured_at
        ) for img in c.images
    ]

    # Map AI Analysis
    ai_resp = None
    if c.ai_analysis:
        ai_resp = AIAnalysisResponse(
            id=c.ai_analysis.id,
            model_name=c.ai_analysis.model_name,
            model_version=c.ai_analysis.model_version,
            detected_category=c.ai_analysis.detected_category,
            confidence=c.ai_analysis.confidence,
            predicted_severity=c.ai_analysis.predicted_severity,
            predicted_priority=c.ai_analysis.predicted_priority,
            predicted_department=c.ai_analysis.predicted_department,
            duplicate_candidates_count=c.ai_analysis.duplicate_candidates_count,
            contributing_factors=c.ai_analysis.contributing_factors,
            explanation_text=c.ai_analysis.explanation_text,
            inference_latency_ms=c.ai_analysis.inference_latency_ms,
            created_at=c.ai_analysis.created_at
        )

    # Map Timeline
    timeline_resp = [
        StatusHistoryResponse(
            id=h.id,
            previous_status=h.previous_status,
            new_status=h.new_status,
            reason=h.reason,
            created_at=h.created_at
        ) for h in sorted(c.status_history, key=lambda x: x.created_at)
    ]

    # Map Comments
    comments_resp = []
    for comm in sorted(c.comments, key=lambda x: x.created_at):
        comments_resp.append(CommentResponse(
            id=comm.id,
            user_id=comm.user_id,
            user_name="Official Authority" if comm.is_official else "Citizen",
            user_role="OFFICIAL" if comm.is_official else "CITIZEN",
            is_official=comm.is_official,
            comment_text=comm.comment_text,
            created_at=comm.created_at
        ))

    # Map Resolution Evidence
    res_evidence_resp = None
    if c.resolution_evidence:
        res_evidence_resp = ResolutionEvidenceResponse(
            id=c.resolution_evidence.id,
            officer_name=c.resolution_evidence.officer.user.full_name if c.resolution_evidence.officer and c.resolution_evidence.officer.user else "Authority Officer",
            evidence_image_url=c.resolution_evidence.evidence_image_url,
            evidence_thumbnail_url=c.resolution_evidence.evidence_thumbnail_url,
            completion_note=c.resolution_evidence.completion_note,
            completed_at=c.resolution_evidence.completed_at,
            visual_similarity_score=c.resolution_evidence.visual_similarity_score
        )

    # Map Duplicate Candidates
    dup_candidates_resp = []
    for dup in c.duplicate_candidates:
        cand_img = next((i.image_url for i in dup.candidate.images if i.is_primary), dup.candidate.images[0].image_url if dup.candidate.images else None) if dup.candidate else None
        dup_candidates_resp.append(DuplicateCandidateResponse(
            id=dup.id,
            candidate_complaint_id=dup.candidate_complaint_id,
            candidate_complaint_number=dup.candidate.complaint_number if dup.candidate else "",
            candidate_title=dup.candidate.title if dup.candidate else "",
            candidate_status=dup.candidate.status if dup.candidate else ComplaintStatus.SUBMITTED,
            candidate_image_url=cand_img,
            similarity_score=dup.similarity_score,
            image_similarity=dup.image_similarity,
            text_similarity=dup.text_similarity,
            geo_distance_meters=dup.geo_distance_meters,
            status=dup.status
        ))

    # Anonymize citizen name for regular public or other citizens
    citizen_display_name = c.citizen.user.full_name if (current_user.role in (UserRole.ADMIN, UserRole.OFFICER) or (c.citizen and c.citizen.user_id == current_user.id)) else "Verified Citizen"

    jurisdiction_info = f"{c.jurisdiction.city}, {c.jurisdiction.zone} - Ward {c.jurisdiction.ward}" if c.jurisdiction else None

    detail = ComplaintDetailResponse(
        id=c.id,
        complaint_number=c.complaint_number,
        citizen_id=c.citizen_id,
        citizen_name=citizen_display_name,
        category_id=c.category_id,
        category_name=c.category.name if c.category else None,
        department_id=c.department_id,
        department_name=c.department.name if c.department else None,
        jurisdiction_id=c.jurisdiction_id,
        jurisdiction_info=jurisdiction_info,
        assigned_officer_id=c.assigned_officer_id,
        assigned_officer_name=c.assigned_officer.user.full_name if c.assigned_officer and c.assigned_officer.user else None,
        title=c.title,
        description=c.description,
        status=c.status,
        priority=c.priority,
        severity=c.severity,
        ai_analyzed=c.ai_analyzed,
        ai_status=c.ai_status,
        is_duplicate=c.is_duplicate,
        duplicate_of_id=c.duplicate_of_id,
        duplicate_score=c.duplicate_score,
        requires_manual_verification=c.requires_manual_verification,
        resolution_rating=c.resolution_rating,
        citizen_feedback=c.citizen_feedback,
        citizen_verified=c.citizen_verified,
        reopened_count=c.reopened_count,
        sla_deadline=c.sla_deadline,
        location=loc_resp,
        images=images_resp,
        ai_analysis=ai_resp,
        timeline=timeline_resp,
        comments=comments_resp,
        resolution_evidence=res_evidence_resp,
        duplicate_candidates=dup_candidates_resp,
        created_at=c.created_at,
        updated_at=c.updated_at
    )

    return ResponseBase(success=True, data=detail)

@router.patch("/{id}/status", response_model=ResponseBase[ComplaintListItemResponse])
async def update_complaint_status(
    id: str,
    data: ComplaintStatusUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    complaint = await complaint_service.update_status(
        db=db,
        complaint_id=id,
        user=current_user,
        new_status=data.new_status,
        reason=data.reason
    )
    return ResponseBase(
        success=True,
        message=f"Status changed to {complaint.status.value}",
        data=ComplaintListItemResponse(
            id=complaint.id,
            complaint_number=complaint.complaint_number,
            title=complaint.title,
            status=complaint.status,
            priority=complaint.priority,
            severity=complaint.severity,
            is_duplicate=complaint.is_duplicate,
            created_at=complaint.created_at,
            updated_at=complaint.updated_at
        )
    )

@router.post("/{id}/assign", response_model=ResponseBase[ComplaintListItemResponse])
async def assign_complaint(
    id: str,
    data: ComplaintAssignmentRequest,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.OFFICER)),
    db: AsyncSession = Depends(get_db)
):
    complaint = await complaint_service.assign_complaint(
        db=db,
        complaint_id=id,
        user=current_user,
        data=data
    )
    return ResponseBase(
        success=True,
        message="Complaint assigned successfully",
        data=ComplaintListItemResponse(
            id=complaint.id,
            complaint_number=complaint.complaint_number,
            title=complaint.title,
            status=complaint.status,
            priority=complaint.priority,
            severity=complaint.severity,
            is_duplicate=complaint.is_duplicate,
            created_at=complaint.created_at,
            updated_at=complaint.updated_at
        )
    )

@router.post("/{id}/resolution", response_model=ResponseBase[ResolutionEvidenceResponse])
async def submit_resolution(
    id: str,
    completion_note: str = Form(...),
    evidence_image: UploadFile = File(...),
    current_user: User = Depends(require_roles(UserRole.OFFICER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    img_url, thumb_url, size, mime, img_hash = await storage_service.save_upload_file(evidence_image)
    
    evidence = await complaint_service.submit_resolution(
        db=db,
        complaint_id=id,
        officer_user=current_user,
        evidence_image_url=img_url,
        completion_note=completion_note,
        thumbnail_url=thumb_url
    )

    return ResponseBase(
        success=True,
        message="Resolution evidence submitted. Citizen verification requested.",
        data=ResolutionEvidenceResponse(
            id=evidence.id,
            officer_name=current_user.full_name,
            evidence_image_url=evidence.evidence_image_url,
            evidence_thumbnail_url=evidence.evidence_thumbnail_url,
            completion_note=evidence.completion_note,
            completed_at=evidence.completed_at,
            visual_similarity_score=evidence.visual_similarity_score,
            ai_visual_diff_score=evidence.ai_visual_diff_score,
            ai_resolution_confidence=evidence.ai_resolution_confidence,
            ai_likely_resolved=evidence.ai_likely_resolved
        )
    )

@router.post("/{id}/verify", response_model=ResponseBase[ComplaintListItemResponse])
async def verify_resolution(
    id: str,
    data: CitizenVerificationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    complaint = await complaint_service.verify_resolution(
        db=db,
        complaint_id=id,
        citizen_user=current_user,
        data=data
    )
    action_str = "confirmed resolved" if data.is_resolved else "reopened"
    return ResponseBase(
        success=True,
        message=f"Complaint {complaint.complaint_number} {action_str}.",
        data=ComplaintListItemResponse(
            id=complaint.id,
            complaint_number=complaint.complaint_number,
            title=complaint.title,
            status=complaint.status,
            priority=complaint.priority,
            severity=complaint.severity,
            is_duplicate=complaint.is_duplicate,
            created_at=complaint.created_at,
            updated_at=complaint.updated_at
        )
    )

@router.post("/{id}/comments", response_model=ResponseBase[CommentResponse])
async def add_comment(
    id: str,
    data: CommentCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    comment = await complaint_service.add_comment(
        db=db,
        complaint_id=id,
        user=current_user,
        comment_text=data.comment_text
    )
    return ResponseBase(
        success=True,
        message="Comment posted successfully",
        data=CommentResponse(
            id=comment.id,
            user_id=comment.user_id,
            user_name=current_user.full_name,
            user_role=current_user.role.value,
            is_official=comment.is_official,
            comment_text=comment.comment_text,
            created_at=comment.created_at
        )
    )
