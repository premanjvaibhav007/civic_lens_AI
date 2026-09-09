import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean, DateTime,
    ForeignKey, Enum, Index, JSON, UniqueConstraint
)
from sqlalchemy.orm import relationship
from backend.app.db.session import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

class UserRole(str, enum.Enum):
    CITIZEN = "CITIZEN"
    OFFICER = "OFFICER"
    ADMIN = "ADMIN"

class ComplaintStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    AI_ANALYZING = "AI_ANALYZING"
    AI_VERIFIED = "AI_VERIFIED"
    ROUTED = "ROUTED"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLUTION_SUBMITTED = "RESOLUTION_SUBMITTED"
    CITIZEN_VERIFICATION = "CITIZEN_VERIFICATION"
    RESOLVED = "RESOLVED"
    REJECTED = "REJECTED"
    DUPLICATE = "DUPLICATE"
    ESCALATED = "ESCALATED"
    REOPENED = "REOPENED"

class SeverityLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class PriorityLevel(str, enum.Enum):
    P1 = "P1" # Critical
    P2 = "P2" # High
    P3 = "P3" # Medium
    P4 = "P4" # Low

class AIStatus(str, enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"

class DuplicateStatus(str, enum.Enum):
    POTENTIAL = "POTENTIAL"
    CONFIRMED_DUPLICATE = "CONFIRMED_DUPLICATE"
    REJECTED = "REJECTED"

# ==============================================================================
# 1. USER & CITIZEN & OFFICER MODELS
# ==============================================================================

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(30), unique=True, index=True, nullable=True)
    role = Column(Enum(UserRole), default=UserRole.CITIZEN, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    citizen_profile = relationship("Citizen", back_populates="user", uselist=False, cascade="all, delete-orphan")
    officer_profile = relationship("Officer", back_populates="user", uselist=False, cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")

class Citizen(Base):
    __tablename__ = "citizens"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    default_city = Column(String(100), nullable=True)
    total_reports = Column(Integer, default=0, nullable=False)
    verified_reports = Column(Integer, default=0, nullable=False)
    badge_score = Column(Integer, default=10, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", back_populates="citizen_profile")
    complaints = relationship("Complaint", back_populates="citizen")

class Department(Base):
    __tablename__ = "departments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(150), unique=True, nullable=False)
    code = Column(String(50), unique=True, index=True, nullable=False) # e.g. ROADS, ELECTRICAL, SANITATION
    description = Column(Text, nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(30), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    officers = relationship("Officer", back_populates="department")
    categories = relationship("Category", back_populates="default_department")
    complaints = relationship("Complaint", back_populates="department")

class Jurisdiction(Base):
    __tablename__ = "jurisdictions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    city = Column(String(100), index=True, nullable=False)
    zone = Column(String(100), index=True, nullable=False)
    ward = Column(String(100), index=True, nullable=False)
    boundary_geojson = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint('city', 'zone', 'ward', name='uix_city_zone_ward'),
    )

    officers = relationship("Officer", back_populates="jurisdiction")
    complaints = relationship("Complaint", back_populates="jurisdiction")

class Officer(Base):
    __tablename__ = "officers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    department_id = Column(String(36), ForeignKey("departments.id"), nullable=False)
    jurisdiction_id = Column(String(36), ForeignKey("jurisdictions.id"), nullable=True)
    badge_number = Column(String(50), unique=True, index=True, nullable=False)
    designation = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", back_populates="officer_profile")
    department = relationship("Department", back_populates="officers")
    jurisdiction = relationship("Jurisdiction", back_populates="officers")
    assigned_complaints = relationship("Complaint", back_populates="assigned_officer")
    resolution_evidences = relationship("ResolutionEvidence", back_populates="officer")

# ==============================================================================
# 2. CATEGORY & ROUTING & SLA RULES
# ==============================================================================

class Category(Base):
    __tablename__ = "categories"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), unique=True, nullable=False)
    code = Column(String(50), unique=True, index=True, nullable=False) # e.g. POTHOLE, GARBAGE, STREETLIGHT
    description = Column(Text, nullable=True)
    default_department_id = Column(String(36), ForeignKey("departments.id"), nullable=True)
    default_priority = Column(Enum(PriorityLevel), default=PriorityLevel.P3, nullable=False)
    default_severity = Column(Enum(SeverityLevel), default=SeverityLevel.MEDIUM, nullable=False)
    icon_name = Column(String(50), default="alert-circle", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    default_department = relationship("Department", back_populates="categories")
    complaints = relationship("Complaint", back_populates="category")

class RoutingRule(Base):
    __tablename__ = "routing_rules"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(150), nullable=False)
    category_id = Column(String(36), ForeignKey("categories.id"), nullable=True)
    jurisdiction_id = Column(String(36), ForeignKey("jurisdictions.id"), nullable=True)
    target_department_id = Column(String(36), ForeignKey("departments.id"), nullable=False)
    priority_boost = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

class SLARule(Base):
    __tablename__ = "sla_rules"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    category_id = Column(String(36), ForeignKey("categories.id"), nullable=True)
    priority = Column(Enum(PriorityLevel), nullable=False)
    resolution_time_hours = Column(Integer, default=48, nullable=False)
    escalation_time_hours = Column(Integer, default=72, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

# ==============================================================================
# 3. COMPLAINTS & LOCATION & IMAGES & AI ANALYSIS
# ==============================================================================

class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    complaint_number = Column(String(30), unique=True, index=True, nullable=False) # e.g. CL-2026-00001
    citizen_id = Column(String(36), ForeignKey("citizens.id"), nullable=False, index=True)
    category_id = Column(String(36), ForeignKey("categories.id"), nullable=True, index=True)
    department_id = Column(String(36), ForeignKey("departments.id"), nullable=True, index=True)
    jurisdiction_id = Column(String(36), ForeignKey("jurisdictions.id"), nullable=True, index=True)
    assigned_officer_id = Column(String(36), ForeignKey("officers.id"), nullable=True, index=True)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(ComplaintStatus), default=ComplaintStatus.SUBMITTED, nullable=False, index=True)
    priority = Column(Enum(PriorityLevel), default=PriorityLevel.P3, nullable=False, index=True)
    severity = Column(Enum(SeverityLevel), default=SeverityLevel.MEDIUM, nullable=False, index=True)

    # AI tracking
    ai_analyzed = Column(Boolean, default=False, nullable=False)
    ai_status = Column(Enum(AIStatus), default=AIStatus.PENDING, nullable=False)
    
    # Duplication tracking
    duplicate_of_id = Column(String(36), ForeignKey("complaints.id"), nullable=True)
    is_duplicate = Column(Boolean, default=False, nullable=False, index=True)
    duplicate_score = Column(Float, default=0.0, nullable=False)

    submission_channel = Column(String(50), default="ANDROID_APP", nullable=False)
    requires_manual_verification = Column(Boolean, default=False, nullable=False)

    # Verification loop
    resolution_rating = Column(Integer, nullable=True) # 1 to 5
    citizen_feedback = Column(Text, nullable=True)
    citizen_verified = Column(Boolean, nullable=True)
    reopened_count = Column(Integer, default=0, nullable=False)

    # Civic Incident linkage
    civic_incident_id = Column(String(36), ForeignKey("civic_incidents.id", ondelete="SET NULL"), nullable=True, index=True)

    sla_deadline = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    citizen = relationship("Citizen", back_populates="complaints")
    category = relationship("Category", back_populates="complaints")
    department = relationship("Department", back_populates="complaints")
    jurisdiction = relationship("Jurisdiction", back_populates="complaints")
    assigned_officer = relationship("Officer", back_populates="assigned_complaints")
    civic_incident = relationship("CivicIncident", foreign_keys=[civic_incident_id])

    location = relationship("ComplaintLocation", back_populates="complaint", uselist=False, cascade="all, delete-orphan")
    images = relationship("ComplaintImage", back_populates="complaint", cascade="all, delete-orphan")
    ai_analysis = relationship("ComplaintAIAnalysis", back_populates="complaint", uselist=False, cascade="all, delete-orphan")
    assignments = relationship("ComplaintAssignment", back_populates="complaint", cascade="all, delete-orphan")
    status_history = relationship("ComplaintStatusHistory", back_populates="complaint", cascade="all, delete-orphan")
    comments = relationship("ComplaintComment", back_populates="complaint", cascade="all, delete-orphan")
    resolution_evidence = relationship("ResolutionEvidence", back_populates="complaint", uselist=False, cascade="all, delete-orphan")
    duplicate_candidates = relationship("DuplicateCandidate", foreign_keys="DuplicateCandidate.complaint_id", back_populates="complaint", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_complaint_status_dept", "status", "department_id"),
        Index("ix_complaint_created_priority", "created_at", "priority"),
    )

class ComplaintLocation(Base):
    __tablename__ = "complaint_locations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    complaint_id = Column(String(36), ForeignKey("complaints.id", ondelete="CASCADE"), unique=True, nullable=False)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    accuracy_meters = Column(Float, default=0.0, nullable=False)
    address = Column(Text, nullable=True)
    landmark = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True, index=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    is_manual_adjusted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    complaint = relationship("Complaint", back_populates="location")

    __table_args__ = (
        Index("ix_complaint_lat_lng", "latitude", "longitude"),
    )

class ComplaintImage(Base):
    __tablename__ = "complaint_images"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    complaint_id = Column(String(36), ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False, index=True)
    image_url = Column(String(500), nullable=False)
    thumbnail_url = Column(String(500), nullable=True)
    file_size_bytes = Column(Integer, default=0, nullable=False)
    mime_type = Column(String(100), default="image/jpeg", nullable=False)
    image_hash = Column(String(64), nullable=True, index=True)
    is_primary = Column(Boolean, default=True, nullable=False)
    captured_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    complaint = relationship("Complaint", back_populates="images")

class ComplaintAIAnalysis(Base):
    __tablename__ = "complaint_ai_analysis"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    complaint_id = Column(String(36), ForeignKey("complaints.id", ondelete="CASCADE"), unique=True, nullable=False)
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(50), nullable=False)
    detected_category = Column(String(100), nullable=False)
    confidence = Column(Float, nullable=False)
    predicted_severity = Column(Enum(SeverityLevel), nullable=False)
    predicted_priority = Column(Enum(PriorityLevel), nullable=False)
    predicted_department = Column(String(100), nullable=True)
    duplicate_candidates_count = Column(Integer, default=0, nullable=False)
    contributing_factors = Column(JSON, nullable=True) # {"damage_size": 0.8, "major_road": True, ...}
    explanation_text = Column(Text, nullable=True)
    raw_inference_json = Column(JSON, nullable=True)
    inference_latency_ms = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    complaint = relationship("Complaint", back_populates="ai_analysis")

class ComplaintAssignment(Base):
    __tablename__ = "complaint_assignments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    complaint_id = Column(String(36), ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_by_user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    department_id = Column(String(36), ForeignKey("departments.id"), nullable=False)
    officer_id = Column(String(36), ForeignKey("officers.id"), nullable=True)
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    complaint = relationship("Complaint", back_populates="assignments")

class ComplaintStatusHistory(Base):
    __tablename__ = "complaint_status_history"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    complaint_id = Column(String(36), ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False, index=True)
    changed_by_user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    previous_status = Column(Enum(ComplaintStatus), nullable=True)
    new_status = Column(Enum(ComplaintStatus), nullable=False)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    complaint = relationship("Complaint", back_populates="status_history")

class ComplaintComment(Base):
    __tablename__ = "complaint_comments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    complaint_id = Column(String(36), ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    is_official = Column(Boolean, default=False, nullable=False)
    comment_text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    complaint = relationship("Complaint", back_populates="comments")

class ResolutionEvidence(Base):
    __tablename__ = "resolution_evidence"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    complaint_id = Column(String(36), ForeignKey("complaints.id", ondelete="CASCADE"), unique=True, nullable=False)
    officer_id = Column(String(36), ForeignKey("officers.id"), nullable=False)
    evidence_image_url = Column(String(500), nullable=False)
    evidence_thumbnail_url = Column(String(500), nullable=True)
    completion_note = Column(Text, nullable=False)
    completed_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    visual_similarity_score = Column(Float, nullable=True)
    ai_visual_diff_score = Column(Float, nullable=True) # 0–100 diff percentage
    ai_resolution_confidence = Column(Float, nullable=True) # 0.0–1.0
    ai_likely_resolved = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    complaint = relationship("Complaint", back_populates="resolution_evidence")
    officer = relationship("Officer", back_populates="resolution_evidences")

class DuplicateCandidate(Base):
    __tablename__ = "duplicate_candidates"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    complaint_id = Column(String(36), ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_complaint_id = Column(String(36), ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False, index=True)
    similarity_score = Column(Float, nullable=False)
    image_similarity = Column(Float, default=0.0, nullable=False)
    text_similarity = Column(Float, default=0.0, nullable=False)
    geo_distance_meters = Column(Float, default=0.0, nullable=False)
    status = Column(Enum(DuplicateStatus), default=DuplicateStatus.POTENTIAL, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    complaint = relationship("Complaint", foreign_keys=[complaint_id], back_populates="duplicate_candidates")
    candidate = relationship("Complaint", foreign_keys=[candidate_complaint_id])

# ==============================================================================
# 4. NOTIFICATIONS, AUDIT LOGS & MODEL VERSIONS
# ==============================================================================

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    complaint_id = Column(String(36), ForeignKey("complaints.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), default="STATUS_UPDATE", nullable=False)
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    user = relationship("User", back_populates="notifications")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True) # e.g. STATUS_CHANGE, ASSIGNMENT, VERIFICATION
    entity_name = Column(String(100), nullable=False, index=True) # e.g. Complaint, Officer
    entity_id = Column(String(36), nullable=False, index=True)
    old_value_json = Column(JSON, nullable=True)
    new_value_json = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    user = relationship("User", back_populates="audit_logs")

class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    model_name = Column(String(100), nullable=False, index=True)
    version = Column(String(50), nullable=False)
    task_type = Column(String(50), nullable=False) # e.g. CLASSIFICATION, SEVERITY, DUPLICATE
    weights_path = Column(String(255), nullable=True)
    metrics_json = Column(JSON, nullable=True) # {"accuracy": 0.94, "f1": 0.92, ...}
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint('model_name', 'version', name='uix_model_name_version'),
    )

# ==============================================================================
# 5. CIVIC INCIDENT & INFRASTRUCTURE ASSET MODELS (Stage 3 Additions)
# ==============================================================================

class IncidentStatus(str, enum.Enum):
    OPEN = "OPEN"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    REOPENED = "REOPENED"

class AssetType(str, enum.Enum):
    ROAD = "ROAD"
    STREETLIGHT = "STREETLIGHT"
    DRAIN = "DRAIN"
    FOOTPATH = "FOOTPATH"
    TRAFFIC_SIGN = "TRAFFIC_SIGN"
    BUS_STOP = "BUS_STOP"
    WATER_INFRASTRUCTURE = "WATER_INFRASTRUCTURE"
    PUBLIC_TOILET = "PUBLIC_TOILET"
    PARK_FACILITY = "PARK_FACILITY"
    MANHOLE = "MANHOLE"
    OTHER = "OTHER"

class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class CivicIncident(Base):
    """
    A CivicIncident clusters one or more citizen reports referring to
    the same physical infrastructure problem. Multiple Complaints can
    be linked to the same CivicIncident.
    """
    __tablename__ = "civic_incidents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    incident_number = Column(String(30), unique=True, index=True, nullable=False)  # INC-2026-00001
    category_id = Column(String(36), ForeignKey("categories.id"), nullable=True, index=True)
    department_id = Column(String(36), ForeignKey("departments.id"), nullable=True, index=True)
    jurisdiction_id = Column(String(36), ForeignKey("jurisdictions.id"), nullable=True, index=True)
    assigned_officer_id = Column(String(36), ForeignKey("officers.id"), nullable=True, index=True)
    infrastructure_asset_id = Column(String(36), ForeignKey("infrastructure_assets.id"), nullable=True)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(IncidentStatus), default=IncidentStatus.OPEN, nullable=False, index=True)
    severity = Column(Enum(SeverityLevel), default=SeverityLevel.MEDIUM, nullable=False, index=True)
    priority = Column(Enum(PriorityLevel), default=PriorityLevel.P3, nullable=False, index=True)

    # Geo centre of all linked reports
    centroid_lat = Column(Float, nullable=True, index=True)
    centroid_lng = Column(Float, nullable=True, index=True)
    ward = Column(String(100), nullable=True, index=True)
    city = Column(String(100), nullable=True, index=True)

    # Civic Intelligence
    civic_impact_score = Column(Float, default=0.0, nullable=False)  # 0–100
    impact_breakdown_json = Column(JSON, nullable=True)              # {safety: 22, population: 18, ...}
    priority_explanation = Column(Text, nullable=True)

    # Aggregated stats (denormalised for performance)
    report_count = Column(Integer, default=1, nullable=False)
    duplicate_count = Column(Integer, default=0, nullable=False)
    recurrence_count = Column(Integer, default=0, nullable=False)
    ai_confidence = Column(Float, default=0.0, nullable=False)
    model_name = Column(String(100), nullable=True)
    model_version = Column(String(50), nullable=True)

    first_reported_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    last_updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    sla_deadline = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    # Relationships
    category = relationship("Category")
    department = relationship("Department")
    jurisdiction = relationship("Jurisdiction")
    assigned_officer = relationship("Officer")
    infrastructure_asset = relationship("InfrastructureAsset", back_populates="incidents")
    incident_reports = relationship("IncidentReport", back_populates="incident", cascade="all, delete-orphan")
    status_history = relationship("IncidentStatusHistory", back_populates="incident", cascade="all, delete-orphan")
    predictions = relationship("IncidentPrediction", back_populates="incident", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_incident_status_dept", "status", "department_id"),
        Index("ix_incident_centroid", "centroid_lat", "centroid_lng"),
        Index("ix_incident_severity_priority", "severity", "priority"),
    )


class InfrastructureAsset(Base):
    """
    Tracks a physical infrastructure asset (road segment, streetlight, drain, etc.)
    that can be associated with multiple civic incidents over its lifetime.
    """
    __tablename__ = "infrastructure_assets"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    asset_code = Column(String(50), unique=True, index=True, nullable=False)
    asset_type = Column(Enum(AssetType), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    department_id = Column(String(36), ForeignKey("departments.id"), nullable=True)
    jurisdiction_id = Column(String(36), ForeignKey("jurisdictions.id"), nullable=True)

    # Location
    latitude = Column(Float, nullable=True, index=True)
    longitude = Column(Float, nullable=True, index=True)
    address = Column(Text, nullable=True)

    # Health tracking
    health_score = Column(Float, default=100.0, nullable=False)  # 0–100
    risk_score = Column(Float, default=0.0, nullable=False)       # 0–100
    risk_level = Column(Enum(RiskLevel), default=RiskLevel.LOW, nullable=False)

    # Repair history
    complaint_count = Column(Integer, default=0, nullable=False)
    repair_count = Column(Integer, default=0, nullable=False)
    is_recurrent = Column(Boolean, default=False, nullable=False)
    last_repair_at = Column(DateTime(timezone=True), nullable=True)
    installation_date = Column(DateTime(timezone=True), nullable=True)

    ai_recommendation = Column(String(255), nullable=True)  # e.g. "INSPECTION REQUIRED"
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    department = relationship("Department")
    jurisdiction = relationship("Jurisdiction")
    incidents = relationship("CivicIncident", back_populates="infrastructure_asset")

    __table_args__ = (
        Index("ix_asset_lat_lng", "latitude", "longitude"),
        Index("ix_asset_type_health", "asset_type", "health_score"),
    )


class IncidentReport(Base):
    """
    Join table linking a Complaint (citizen report) to a CivicIncident.
    One complaint can be the canonical report for one incident.
    """
    __tablename__ = "incident_reports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    incident_id = Column(String(36), ForeignKey("civic_incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    complaint_id = Column(String(36), ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False, index=True)
    is_canonical = Column(Boolean, default=False, nullable=False)  # The primary/first report
    similarity_score = Column(Float, default=1.0, nullable=False)   # How similar to canonical report
    linked_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    linked_by_user_id = Column(String(36), ForeignKey("users.id"), nullable=True)

    incident = relationship("CivicIncident", back_populates="incident_reports")
    complaint = relationship("Complaint")

    __table_args__ = (
        UniqueConstraint("incident_id", "complaint_id", name="uix_incident_complaint"),
    )


class IncidentStatusHistory(Base):
    """Tamper-evident audit trail for civic incident status changes."""
    __tablename__ = "incident_status_history"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    incident_id = Column(String(36), ForeignKey("civic_incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    changed_by_user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    previous_status = Column(Enum(IncidentStatus), nullable=True)
    new_status = Column(Enum(IncidentStatus), nullable=False)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    incident = relationship("CivicIncident", back_populates="status_history")


class IncidentPrediction(Base):
    """
    AI-generated infrastructure risk prediction for a civic incident location.
    Only created when PREDICTION_MIN_HISTORY_DAYS of data exists.
    """
    __tablename__ = "incident_predictions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    incident_id = Column(String(36), ForeignKey("civic_incidents.id", ondelete="CASCADE"), nullable=True)
    jurisdiction_id = Column(String(36), ForeignKey("jurisdictions.id"), nullable=True, index=True)
    category_id = Column(String(36), ForeignKey("categories.id"), nullable=True)

    prediction_type = Column(String(50), default="RECURRENCE_RISK", nullable=False)
    risk_score = Column(Float, nullable=False)             # 0–100
    risk_level = Column(Enum(RiskLevel), nullable=False)
    prediction_window_days = Column(Integer, default=14, nullable=False)
    contributing_factors = Column(JSON, nullable=True)    # [{factor, weight, value}, ...]
    confidence = Column(Float, nullable=False)            # 0–1
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    incident = relationship("CivicIncident", back_populates="predictions")
    jurisdiction = relationship("Jurisdiction")
    category = relationship("Category")

