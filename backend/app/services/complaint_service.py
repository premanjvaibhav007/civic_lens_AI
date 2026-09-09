import random
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, desc, or_, and_
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from backend.app.models.entities import (
    Complaint, ComplaintLocation, ComplaintImage, ComplaintStatusHistory,
    ComplaintAssignment, ComplaintComment, ResolutionEvidence, Citizen,
    Department, Jurisdiction, Officer, User, Category,
    ComplaintStatus, SeverityLevel, PriorityLevel, UserRole
)
from backend.app.schemas.complaint import (
    ComplaintCreateRequest, ComplaintStatusUpdateRequest,
    ComplaintAssignmentRequest, ResolutionSubmissionRequest,
    CitizenVerificationRequest, CommentCreateRequest
)
from backend.app.services.audit_service import audit_service
from backend.app.services.notification_service import notification_service

class ComplaintService:
    # State Machine Transition Rules
    VALID_TRANSITIONS: Dict[ComplaintStatus, List[ComplaintStatus]] = {
        ComplaintStatus.DRAFT: [ComplaintStatus.SUBMITTED],
        ComplaintStatus.SUBMITTED: [
            ComplaintStatus.AI_ANALYZING, ComplaintStatus.ROUTED,
            ComplaintStatus.REJECTED, ComplaintStatus.DUPLICATE
        ],
        ComplaintStatus.AI_ANALYZING: [
            ComplaintStatus.AI_VERIFIED, ComplaintStatus.ROUTED,
            ComplaintStatus.SUBMITTED
        ],
        ComplaintStatus.AI_VERIFIED: [
            ComplaintStatus.ROUTED, ComplaintStatus.ASSIGNED
        ],
        ComplaintStatus.ROUTED: [
            ComplaintStatus.ASSIGNED, ComplaintStatus.IN_PROGRESS,
            ComplaintStatus.REJECTED, ComplaintStatus.DUPLICATE
        ],
        ComplaintStatus.ASSIGNED: [
            ComplaintStatus.IN_PROGRESS, ComplaintStatus.REJECTED,
            ComplaintStatus.DUPLICATE, ComplaintStatus.ESCALATED
        ],
        ComplaintStatus.IN_PROGRESS: [
            ComplaintStatus.RESOLUTION_SUBMITTED, ComplaintStatus.ESCALATED,
            ComplaintStatus.ASSIGNED
        ],
        ComplaintStatus.RESOLUTION_SUBMITTED: [
            ComplaintStatus.CITIZEN_VERIFICATION, ComplaintStatus.RESOLVED,
            ComplaintStatus.REOPENED
        ],
        ComplaintStatus.CITIZEN_VERIFICATION: [
            ComplaintStatus.RESOLVED, ComplaintStatus.REOPENED
        ],
        ComplaintStatus.REOPENED: [
            ComplaintStatus.ASSIGNED, ComplaintStatus.IN_PROGRESS,
            ComplaintStatus.ESCALATED
        ],
        ComplaintStatus.ESCALATED: [
            ComplaintStatus.IN_PROGRESS, ComplaintStatus.ASSIGNED,
            ComplaintStatus.RESOLVED
        ],
        ComplaintStatus.RESOLVED: [
            ComplaintStatus.REOPENED # Allowed if citizen rejects resolution within verification period
        ],
        ComplaintStatus.REJECTED: [],
        ComplaintStatus.DUPLICATE: []
    }

    @staticmethod
    async def generate_complaint_number(db: AsyncSession) -> str:
        current_year = datetime.now(timezone.utc).year
        count_stmt = select(func.count(Complaint.id))
        res = await db.execute(count_stmt)
        total_count = res.scalar() or 0
        random_suffix = random.randint(10, 99)
        return f"CL-{current_year}-{(total_count + 1):05d}{random_suffix}"

    @staticmethod
    async def create_complaint(
        db: AsyncSession,
        citizen_user_id: str,
        data: ComplaintCreateRequest,
        image_url: Optional[str] = None,
        thumbnail_url: Optional[str] = None,
        file_size_bytes: int = 0,
        mime_type: str = "image/jpeg",
        image_hash: Optional[str] = None
    ) -> Complaint:
        # Get citizen profile
        cit_stmt = select(Citizen).where(Citizen.user_id == citizen_user_id)
        cit_res = await db.execute(cit_stmt)
        citizen = cit_res.scalars().first()
        if not citizen:
            citizen = Citizen(user_id=citizen_user_id)
            db.add(citizen)
            await db.flush()

        complaint_num = await ComplaintService.generate_complaint_number(db)

        complaint = Complaint(
            complaint_number=complaint_num,
            citizen_id=citizen.id,
            category_id=data.category_id,
            title=data.title,
            description=data.description,
            status=ComplaintStatus.SUBMITTED,
            priority=PriorityLevel.P3,
            severity=SeverityLevel.MEDIUM,
            submission_channel=data.submission_channel
        )
        db.add(complaint)
        await db.flush()

        # Add Location
        location = ComplaintLocation(
            complaint_id=complaint.id,
            latitude=data.location.latitude,
            longitude=data.location.longitude,
            accuracy_meters=data.location.accuracy_meters,
            address=data.location.address,
            landmark=data.location.landmark,
            city=data.location.city or citizen.default_city,
            state=data.location.state,
            postal_code=data.location.postal_code,
            is_manual_adjusted=data.location.is_manual_adjusted
        )
        db.add(location)

        # Add Image if provided
        if image_url:
            image_record = ComplaintImage(
                complaint_id=complaint.id,
                image_url=image_url,
                thumbnail_url=thumbnail_url,
                file_size_bytes=file_size_bytes,
                mime_type=mime_type,
                image_hash=image_hash,
                is_primary=True
            )
            db.add(image_record)

        # Record Initial Status History
        history = ComplaintStatusHistory(
            complaint_id=complaint.id,
            changed_by_user_id=citizen_user_id,
            previous_status=None,
            new_status=ComplaintStatus.SUBMITTED,
            reason="Complaint submitted by citizen"
        )
        db.add(history)

        # Increment citizen report stats
        citizen.total_reports += 1

        # Audit Log
        await audit_service.log_event(
            db=db,
            user_id=citizen_user_id,
            action="COMPLAINT_SUBMITTED",
            entity_name="Complaint",
            entity_id=complaint.id,
            new_value={"complaint_number": complaint_num, "title": data.title}
        )

        # Create Confirmation Notification
        await notification_service.create_notification(
            db=db,
            user_id=citizen_user_id,
            title=f"Complaint {complaint_num} Received",
            message="Your complaint has been successfully recorded and is undergoing automated AI triage.",
            complaint_id=complaint.id,
            notification_type="COMPLAINT_SUBMITTED"
        )

        await db.commit()
        return complaint

    @staticmethod
    async def update_status(
        db: AsyncSession,
        complaint_id: str,
        user: User,
        new_status: ComplaintStatus,
        reason: Optional[str] = None
    ) -> Complaint:
        stmt = select(Complaint).where(Complaint.id == complaint_id)
        res = await db.execute(stmt)
        complaint = res.scalars().first()
        if not complaint:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")

        current_status = complaint.status

        # Server-side validation of state machine transitions
        allowed = ComplaintService.VALID_TRANSITIONS.get(current_status, [])
        if new_status not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status transition from {current_status.value} to {new_status.value}. Allowed: {[s.value for s in allowed]}"
            )

        # Role-based restriction: citizens can only reopen or verify
        if user.role == UserRole.CITIZEN:
            if new_status not in (ComplaintStatus.REOPENED, ComplaintStatus.RESOLVED):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Citizens can only verify or reopen complaints")

        complaint.status = new_status
        history = ComplaintStatusHistory(
            complaint_id=complaint.id,
            changed_by_user_id=user.id,
            previous_status=current_status,
            new_status=new_status,
            reason=reason or f"Status updated to {new_status.value}"
        )
        db.add(history)

        await audit_service.log_event(
            db=db,
            user_id=user.id,
            action="STATUS_CHANGED",
            entity_name="Complaint",
            entity_id=complaint.id,
            old_value={"status": current_status.value},
            new_value={"status": new_status.value, "reason": reason}
        )

        # Notify citizen
        cit_user_stmt = select(Citizen.user_id).where(Citizen.id == complaint.citizen_id)
        cit_user_res = await db.execute(cit_user_stmt)
        cit_user_id = cit_user_res.scalar()

        if cit_user_id and cit_user_id != user.id:
            await notification_service.create_notification(
                db=db,
                user_id=cit_user_id,
                title=f"Update on {complaint.complaint_number}",
                message=f"Status changed to {new_status.value}. {reason or ''}",
                complaint_id=complaint.id,
                notification_type="STATUS_CHANGED"
            )

        await db.commit()
        return complaint

    @staticmethod
    async def assign_complaint(
        db: AsyncSession,
        complaint_id: str,
        user: User,
        data: ComplaintAssignmentRequest
    ) -> Complaint:
        stmt = select(Complaint).where(Complaint.id == complaint_id)
        res = await db.execute(stmt)
        complaint = res.scalars().first()
        if not complaint:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")

        old_dept_id = complaint.department_id
        old_officer_id = complaint.assigned_officer_id

        complaint.department_id = data.department_id
        if data.officer_id:
            complaint.assigned_officer_id = data.officer_id
        if data.priority:
            complaint.priority = data.priority

        # Auto transition to ASSIGNED or IN_PROGRESS
        if complaint.status in (ComplaintStatus.SUBMITTED, ComplaintStatus.ROUTED, ComplaintStatus.AI_VERIFIED):
            complaint.status = ComplaintStatus.ASSIGNED

        assignment = ComplaintAssignment(
            complaint_id=complaint.id,
            assigned_by_user_id=user.id,
            department_id=data.department_id,
            officer_id=data.officer_id,
            remarks=data.remarks
        )
        db.add(assignment)

        history = ComplaintStatusHistory(
            complaint_id=complaint.id,
            changed_by_user_id=user.id,
            previous_status=ComplaintStatus.ROUTED,
            new_status=complaint.status,
            reason=f"Assigned to department by {user.full_name}. Remarks: {data.remarks or 'None'}"
        )
        db.add(history)

        await audit_service.log_event(
            db=db,
            user_id=user.id,
            action="COMPLAINT_ASSIGNED",
            entity_name="Complaint",
            entity_id=complaint.id,
            old_value={"department_id": old_dept_id, "officer_id": old_officer_id},
            new_value={"department_id": data.department_id, "officer_id": data.officer_id, "remarks": data.remarks}
        )

        # Notify assigned officer
        if data.officer_id:
            off_stmt = select(Officer.user_id).where(Officer.id == data.officer_id)
            off_res = await db.execute(off_stmt)
            off_user_id = off_res.scalar()
            if off_user_id:
                await notification_service.create_notification(
                    db=db,
                    user_id=off_user_id,
                    title=f"New Task Assigned: {complaint.complaint_number}",
                    message=f"You have been assigned complaint '{complaint.title}' (Priority: {complaint.priority.value}).",
                    complaint_id=complaint.id,
                    notification_type="OFFICER_ASSIGNED"
                )

        await db.commit()
        return complaint

    @staticmethod
    async def submit_resolution(
        db: AsyncSession,
        complaint_id: str,
        officer_user: User,
        evidence_image_url: str,
        completion_note: str,
        thumbnail_url: Optional[str] = None
    ) -> ResolutionEvidence:
        stmt = select(Complaint).where(Complaint.id == complaint_id)
        res = await db.execute(stmt)
        complaint = res.scalars().first()
        if not complaint:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")

        # Get officer profile
        off_stmt = select(Officer).where(Officer.user_id == officer_user.id)
        off_res = await db.execute(off_stmt)
        officer = off_res.scalars().first()
        if not officer:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only officers can submit resolution evidence")

        # Stage 7: Run AI visual verification between before and after image
        before_img_stmt = select(ComplaintImage).where(
            ComplaintImage.complaint_id == complaint.id,
            ComplaintImage.is_primary == True
        )
        before_img_res = await db.execute(before_img_stmt)
        before_img = before_img_res.scalars().first()

        before_path = f"./storage/uploads/{before_img.image_url.split('/')[-1]}" if before_img else None
        after_path = f"./storage/uploads/{evidence_image_url.split('/')[-1]}"

        from backend.app.services.ai_service import ai_service
        visual_diff = ai_service.verify_resolution_visual(before_path, after_path)

        evidence = ResolutionEvidence(
            complaint_id=complaint.id,
            officer_id=officer.id,
            evidence_image_url=evidence_image_url,
            evidence_thumbnail_url=thumbnail_url,
            completion_note=completion_note,
            completed_at=datetime.now(timezone.utc),
            visual_similarity_score=visual_diff.get("diff_score"),
            ai_visual_diff_score=visual_diff.get("diff_score"),
            ai_resolution_confidence=visual_diff.get("confidence"),
            ai_likely_resolved=visual_diff.get("likely_resolved", True)
        )
        db.add(evidence)

        # Update Complaint Status to RESOLUTION_SUBMITTED / CITIZEN_VERIFICATION
        complaint.status = ComplaintStatus.RESOLUTION_SUBMITTED
        history = ComplaintStatusHistory(
            complaint_id=complaint.id,
            changed_by_user_id=officer_user.id,
            previous_status=ComplaintStatus.IN_PROGRESS,
            new_status=ComplaintStatus.RESOLUTION_SUBMITTED,
            reason=f"Resolution evidence submitted by {officer_user.full_name}: '{completion_note}'"
        )
        db.add(history)

        await audit_service.log_event(
            db=db,
            user_id=officer_user.id,
            action="RESOLUTION_SUBMITTED",
            entity_name="Complaint",
            entity_id=complaint.id,
            new_value={"note": completion_note, "evidence_image": evidence_image_url}
        )

        # Notify Citizen with action request: "Please verify whether the issue has been resolved."
        cit_user_stmt = select(Citizen.user_id).where(Citizen.id == complaint.citizen_id)
        cit_user_res = await db.execute(cit_user_stmt)
        cit_user_id = cit_user_res.scalar()
        if cit_user_id:
            await notification_service.create_notification(
                db=db,
                user_id=cit_user_id,
                title=f"Resolution Submitted for {complaint.complaint_number}",
                message="The authority has submitted repair evidence. Please verify whether the issue has been resolved.",
                complaint_id=complaint.id,
                notification_type="VERIFICATION_REQUEST"
            )

        await db.commit()
        return evidence

    @staticmethod
    async def verify_resolution(
        db: AsyncSession,
        complaint_id: str,
        citizen_user: User,
        data: CitizenVerificationRequest
    ) -> Complaint:
        stmt = select(Complaint).where(Complaint.id == complaint_id)
        res = await db.execute(stmt)
        complaint = res.scalars().first()
        if not complaint:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")

        # Verify caller owns this complaint
        cit_stmt = select(Citizen).where(Citizen.user_id == citizen_user.id)
        cit_res = await db.execute(cit_stmt)
        citizen = cit_res.scalars().first()
        if not citizen or complaint.citizen_id != citizen.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the reporting citizen can verify resolution")

        if data.is_resolved:
            complaint.status = ComplaintStatus.RESOLVED
            complaint.citizen_verified = True
            complaint.resolution_rating = data.rating or 5
            complaint.citizen_feedback = data.feedback
            citizen.verified_reports += 1
            citizen.badge_score += 15

            history = ComplaintStatusHistory(
                complaint_id=complaint.id,
                changed_by_user_id=citizen_user.id,
                previous_status=ComplaintStatus.RESOLUTION_SUBMITTED,
                new_status=ComplaintStatus.RESOLVED,
                reason=f"Citizen confirmed resolution. Rating: {data.rating}/5. Feedback: {data.feedback or 'None'}"
            )
            db.add(history)
        else:
            # Reopen
            complaint.status = ComplaintStatus.REOPENED
            complaint.citizen_verified = False
            complaint.reopened_count += 1
            complaint.citizen_feedback = data.reopen_reason or data.feedback

            history = ComplaintStatusHistory(
                complaint_id=complaint.id,
                changed_by_user_id=citizen_user.id,
                previous_status=ComplaintStatus.RESOLUTION_SUBMITTED,
                new_status=ComplaintStatus.REOPENED,
                reason=f"Citizen reported problem still exists. Reason: {data.reopen_reason or data.feedback or 'Not resolved'}"
            )
            db.add(history)

            # Alert assigned officer
            if complaint.assigned_officer_id:
                off_stmt = select(Officer.user_id).where(Officer.id == complaint.assigned_officer_id)
                off_res = await db.execute(off_stmt)
                off_user_id = off_res.scalar()
                if off_user_id:
                    await notification_service.create_notification(
                        db=db,
                        user_id=off_user_id,
                        title=f"Complaint {complaint.complaint_number} Reopened",
                        message=f"Citizen reported issue still exists: '{data.reopen_reason or 'Verification failed'}'.",
                        complaint_id=complaint.id,
                        notification_type="COMPLAINT_REOPENED"
                    )

        await audit_service.log_event(
            db=db,
            user_id=citizen_user.id,
            action="CITIZEN_VERIFICATION",
            entity_name="Complaint",
            entity_id=complaint.id,
            new_value={
                "is_resolved": data.is_resolved,
                "rating": data.rating,
                "feedback": data.feedback,
                "reopen_reason": data.reopen_reason
            }
        )

        await db.commit()
        return complaint

    @staticmethod
    async def add_comment(
        db: AsyncSession,
        complaint_id: str,
        user: User,
        comment_text: str
    ) -> ComplaintComment:
        stmt = select(Complaint).where(Complaint.id == complaint_id)
        res = await db.execute(stmt)
        complaint = res.scalars().first()
        if not complaint:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")

        is_official = user.role in (UserRole.OFFICER, UserRole.ADMIN)
        comment = ComplaintComment(
            complaint_id=complaint.id,
            user_id=user.id,
            is_official=is_official,
            comment_text=comment_text
        )
        db.add(comment)

        await audit_service.log_event(
            db=db,
            user_id=user.id,
            action="COMMENT_ADDED",
            entity_name="Complaint",
            entity_id=complaint.id,
            new_value={"is_official": is_official, "text": comment_text}
        )

        await db.commit()
        return comment

complaint_service = ComplaintService()
