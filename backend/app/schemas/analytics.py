from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

class OverviewMetrics(BaseModel):
    total_complaints: int
    open_complaints: int
    pending_assignment: int
    in_progress: int
    resolution_submitted: int
    resolved_complaints: int
    escalated_complaints: int
    duplicate_count: int
    average_resolution_hours: float
    sla_compliance_rate: float # percentage e.g. 92.4
    citizen_satisfaction_score: float # 1-5 e.g. 4.2

class CategoryDistributionItem(BaseModel):
    category_id: Optional[str] = None
    category_name: str
    count: int
    percentage: float

class DepartmentPerformanceItem(BaseModel):
    department_id: str
    department_name: str
    total_assigned: int
    resolved_count: int
    in_progress_count: int
    avg_resolution_hours: float
    sla_compliance_rate: float

class StatusTrendItem(BaseModel):
    date: str # YYYY-MM-DD
    submitted: int
    resolved: int
    escalated: int

class GeoHotspotItem(BaseModel):
    latitude: float
    longitude: float
    intensity: float
    complaint_count: int
    category_name: str
    city: str
    ward: Optional[str] = None

class AnalyticsDashboardResponse(BaseModel):
    metrics: OverviewMetrics
    category_distribution: List[CategoryDistributionItem]
    department_performance: List[DepartmentPerformanceItem]
    trend_last_30_days: List[StatusTrendItem]
    geo_hotspots: List[GeoHotspotItem]
