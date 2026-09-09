from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from backend.app.models.entities import (
    ComplaintStatus, SeverityLevel, PriorityLevel,
    AIStatus, DuplicateStatus
)

class LocationCreate(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    accuracy_meters: float = 0.0
    address: Optional[str] = None
    landmark: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    is_manual_adjusted: bool = False

class LocationResponse(BaseModel):
    id: str
    latitude: float
    longitude: float
    accuracy_meters: float
    address: Optional[str] = None
    landmark: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    is_manual_adjusted: bool

class ImageResponse(BaseModel):
    id: str
    image_url: str
    thumbnail_url: Optional[str] = None
    file_size_bytes: int
    mime_type: str
    is_primary: bool
    captured_at: datetime

class AIAnalysisResponse(BaseModel):
    id: str
    model_name: str
    model_version: str
    detected_category: str
    confidence: float
    predicted_severity: SeverityLevel
    predicted_priority: PriorityLevel
    predicted_department: Optional[str] = None
    duplicate_candidates_count: int
    contributing_factors: Optional[Dict[str, Any]] = None
    explanation_text: Optional[str] = None
    inference_latency_ms: float
    created_at: datetime

class DuplicateCandidateResponse(BaseModel):
    id: str
    candidate_complaint_id: str
    candidate_complaint_number: str
    candidate_title: str
    candidate_status: ComplaintStatus
    candidate_image_url: Optional[str] = None
    similarity_score: float
    image_similarity: float
    text_similarity: float
    geo_distance_meters: float
    status: DuplicateStatus

class StatusHistoryResponse(BaseModel):
    id: str
    previous_status: Optional[ComplaintStatus] = None
    new_status: ComplaintStatus
    reason: Optional[str] = None
    changed_by_name: Optional[str] = None
    created_at: datetime

class CommentResponse(BaseModel):
    id: str
    user_id: str
    user_name: str
    user_role: str
    is_official: bool
    comment_text: str
    created_at: datetime

class ResolutionEvidenceResponse(BaseModel):
    id: str
    officer_name: str
    evidence_image_url: str
    evidence_thumbnail_url: Optional[str] = None
    completion_note: str
    completed_at: datetime
    visual_similarity_score: Optional[float] = None
    ai_visual_diff_score: Optional[float] = None
    ai_resolution_confidence: Optional[float] = None
    ai_likely_resolved: Optional[bool] = True

# Request schemas
class ComplaintCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    category_id: Optional[str] = None
    location: LocationCreate
    image_base64: Optional[str] = None # For offline/direct sync or fallback
    image_id: Optional[str] = None
    submission_channel: str = "ANDROID_APP"

class ComplaintUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[str] = None

class ComplaintStatusUpdateRequest(BaseModel):
    new_status: ComplaintStatus
    reason: Optional[str] = None

class ComplaintAssignmentRequest(BaseModel):
    department_id: str
    officer_id: Optional[str] = None
    remarks: Optional[str] = None
    priority: Optional[PriorityLevel] = None

class ResolutionSubmissionRequest(BaseModel):
    evidence_image_id: str
    completion_note: str = Field(..., min_length=5, max_length=1500)

class CitizenVerificationRequest(BaseModel):
    is_resolved: bool
    rating: Optional[int] = Field(None, ge=1, le=5)
    feedback: Optional[str] = Field(None, max_length=1000)
    reopen_reason: Optional[str] = None
    new_image_id: Optional[str] = None

class CommentCreateRequest(BaseModel):
    comment_text: str = Field(..., min_length=1, max_length=1000)

# Complete Detail Response
class ComplaintDetailResponse(BaseModel):
    id: str
    complaint_number: str
    citizen_id: str
    citizen_name: str
    category_id: Optional[str] = None
    category_name: Optional[str] = None
    department_id: Optional[str] = None
    department_name: Optional[str] = None
    jurisdiction_id: Optional[str] = None
    jurisdiction_info: Optional[str] = None
    assigned_officer_id: Optional[str] = None
    assigned_officer_name: Optional[str] = None
    
    title: str
    description: Optional[str] = None
    status: ComplaintStatus
    priority: PriorityLevel
    severity: SeverityLevel
    
    ai_analyzed: bool
    ai_status: AIStatus
    is_duplicate: bool
    duplicate_of_id: Optional[str] = None
    duplicate_score: float
    
    requires_manual_verification: bool
    resolution_rating: Optional[int] = None
    citizen_feedback: Optional[str] = None
    citizen_verified: Optional[bool] = None
    reopened_count: int
    sla_deadline: Optional[datetime] = None
    
    location: Optional[LocationResponse] = None
    images: List[ImageResponse] = []
    ai_analysis: Optional[AIAnalysisResponse] = None
    timeline: List[StatusHistoryResponse] = []
    comments: List[CommentResponse] = []
    resolution_evidence: Optional[ResolutionEvidenceResponse] = None
    duplicate_candidates: List[DuplicateCandidateResponse] = []
    
    created_at: datetime
    updated_at: datetime

class ComplaintListItemResponse(BaseModel):
    id: str
    complaint_number: str
    title: str
    category_name: Optional[str] = None
    department_name: Optional[str] = None
    status: ComplaintStatus
    priority: PriorityLevel
    severity: SeverityLevel
    primary_image_url: Optional[str] = None
    primary_thumbnail_url: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    city: Optional[str] = None
    is_duplicate: bool
    ai_confidence: Optional[float] = None
    created_at: datetime
    updated_at: datetime
