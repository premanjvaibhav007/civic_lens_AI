from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from backend.app.models.entities import PriorityLevel, SeverityLevel, UserRole

class DepartmentCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    code: str = Field(..., min_length=2, max_length=50)
    description: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None

class DepartmentResponse(BaseModel):
    id: str
    name: str
    code: str
    description: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    is_active: bool
    officer_count: int = 0
    active_complaints_count: int = 0
    created_at: datetime

class JurisdictionCreate(BaseModel):
    city: str = Field(..., min_length=2, max_length=100)
    zone: str = Field(..., min_length=2, max_length=100)
    ward: str = Field(..., min_length=1, max_length=100)
    boundary_geojson: Optional[Dict[str, Any]] = None

class JurisdictionResponse(BaseModel):
    id: str
    city: str
    zone: str
    ward: str
    boundary_geojson: Optional[Dict[str, Any]] = None
    is_active: bool
    created_at: datetime

class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    code: str = Field(..., min_length=2, max_length=50)
    description: Optional[str] = None
    default_department_id: Optional[str] = None
    default_priority: PriorityLevel = PriorityLevel.P3
    default_severity: SeverityLevel = SeverityLevel.MEDIUM
    icon_name: str = "alert-circle"

class CategoryResponse(BaseModel):
    id: str
    name: str
    code: str
    description: Optional[str] = None
    default_department_id: Optional[str] = None
    default_department_name: Optional[str] = None
    default_priority: PriorityLevel
    default_severity: SeverityLevel
    icon_name: str
    is_active: bool
    created_at: datetime

class RoutingRuleCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    category_id: Optional[str] = None
    jurisdiction_id: Optional[str] = None
    target_department_id: str
    priority_boost: int = 0

class RoutingRuleResponse(BaseModel):
    id: str
    name: str
    category_id: Optional[str] = None
    category_name: Optional[str] = None
    jurisdiction_id: Optional[str] = None
    jurisdiction_info: Optional[str] = None
    target_department_id: str
    target_department_name: str
    priority_boost: int
    is_active: bool
    created_at: datetime

class SLARuleCreate(BaseModel):
    category_id: Optional[str] = None
    priority: PriorityLevel
    resolution_time_hours: int = Field(..., gt=0)
    escalation_time_hours: int = Field(..., gt=0)

class SLARuleResponse(BaseModel):
    id: str
    category_id: Optional[str] = None
    category_name: Optional[str] = None
    priority: PriorityLevel
    resolution_time_hours: int
    escalation_time_hours: int
    is_active: bool

class AuditLogResponse(BaseModel):
    id: str
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    action: str
    entity_name: str
    entity_id: str
    old_value_json: Optional[Any] = None
    new_value_json: Optional[Any] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime
