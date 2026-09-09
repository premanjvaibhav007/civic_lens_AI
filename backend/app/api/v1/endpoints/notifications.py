from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import get_db
from backend.app.models.entities import User
from backend.app.schemas.common import ResponseBase
from backend.app.core.security import get_current_user
from backend.app.services.notification_service import notification_service

router = APIRouter(prefix="/notifications", tags=["Notifications"])

class NotificationItem(BaseModel):
    id: str
    complaint_id: Optional[str] = None
    title: str
    message: str
    notification_type: str
    is_read: bool
    created_at: datetime

@router.get("", response_model=ResponseBase[List[NotificationItem]])
async def list_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    notifs = await notification_service.get_user_notifications(
        db=db,
        user_id=current_user.id,
        unread_only=unread_only,
        limit=limit
    )
    items = [
        NotificationItem(
            id=n.id,
            complaint_id=n.complaint_id,
            title=n.title,
            message=n.message,
            notification_type=n.notification_type,
            is_read=n.is_read,
            created_at=n.created_at
        ) for n in notifs
    ]
    return ResponseBase(success=True, data=items)

@router.patch("/{id}/read", response_model=ResponseBase[bool])
async def mark_notification_read(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    success = await notification_service.mark_as_read(db=db, notification_id=id, user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return ResponseBase(success=True, message="Marked as read", data=True)

@router.post("/read-all", response_model=ResponseBase[int])
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    count = await notification_service.mark_all_as_read(db=db, user_id=current_user.id)
    return ResponseBase(success=True, message=f"{count} notifications marked as read", data=count)
