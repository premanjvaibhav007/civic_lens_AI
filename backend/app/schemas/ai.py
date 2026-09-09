from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from backend.app.models.entities import SeverityLevel, PriorityLevel, AIStatus

class AIInferenceRequest(BaseModel):
    image_url: Optional[str] = None
    image_path: Optional[str] = None
    title: str
    description: Optional[str] = None
    latitude: float
    longitude: float

class AIInferenceResult(BaseModel):
    model_name: str
    model_version: str
    status: AIStatus
    detected_category: str
    confidence: float
    predicted_severity: SeverityLevel
    predicted_priority: PriorityLevel
    predicted_department: Optional[str] = None
    contributing_factors: Dict[str, Any]
    explanation_text: str
    duplicate_candidates: List[Dict[str, Any]] = []
    inference_latency_ms: float
