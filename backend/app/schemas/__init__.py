from backend.app.schemas.common import ResponseBase, PaginatedResponse, ErrorResponse
from backend.app.schemas.auth import (
    CitizenRegisterRequest, OfficerRegisterRequest, LoginRequest,
    TokenResponse, RefreshTokenRequest, UserSummaryResponse, PasswordChangeRequest
)
from backend.app.schemas.complaint import (
    ComplaintCreateRequest, ComplaintUpdateRequest, ComplaintStatusUpdateRequest,
    ComplaintAssignmentRequest, ResolutionSubmissionRequest, CitizenVerificationRequest,
    CommentCreateRequest, ComplaintDetailResponse, ComplaintListItemResponse,
    LocationCreate, LocationResponse, ImageResponse, AIAnalysisResponse,
    DuplicateCandidateResponse, StatusHistoryResponse, CommentResponse,
    ResolutionEvidenceResponse
)
from backend.app.schemas.admin import (
    DepartmentCreate, DepartmentResponse, JurisdictionCreate, JurisdictionResponse,
    CategoryCreate, CategoryResponse, RoutingRuleCreate, RoutingRuleResponse,
    SLARuleCreate, SLARuleResponse, AuditLogResponse
)
from backend.app.schemas.analytics import (
    OverviewMetrics, AnalyticsDashboardResponse, CategoryDistributionItem,
    DepartmentPerformanceItem, StatusTrendItem, GeoHotspotItem
)
from backend.app.schemas.ai import AIInferenceRequest, AIInferenceResult

__all__ = [
    "ResponseBase", "PaginatedResponse", "ErrorResponse",
    "CitizenRegisterRequest", "OfficerRegisterRequest", "LoginRequest",
    "TokenResponse", "RefreshTokenRequest", "UserSummaryResponse", "PasswordChangeRequest",
    "ComplaintCreateRequest", "ComplaintUpdateRequest", "ComplaintStatusUpdateRequest",
    "ComplaintAssignmentRequest", "ResolutionSubmissionRequest", "CitizenVerificationRequest",
    "CommentCreateRequest", "ComplaintDetailResponse", "ComplaintListItemResponse",
    "LocationCreate", "LocationResponse", "ImageResponse", "AIAnalysisResponse",
    "DuplicateCandidateResponse", "StatusHistoryResponse", "CommentResponse",
    "ResolutionEvidenceResponse",
    "DepartmentCreate", "DepartmentResponse", "JurisdictionCreate", "JurisdictionResponse",
    "CategoryCreate", "CategoryResponse", "RoutingRuleCreate", "RoutingRuleResponse",
    "SLARuleCreate", "SLARuleResponse", "AuditLogResponse",
    "OverviewMetrics", "AnalyticsDashboardResponse", "CategoryDistributionItem",
    "DepartmentPerformanceItem", "StatusTrendItem", "GeoHotspotItem",
    "AIInferenceRequest", "AIInferenceResult"
]
