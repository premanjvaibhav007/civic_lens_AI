from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    APP_NAME: str = "CivicLens AI"
    APP_VERSION: str = "2.0.0"
    API_V1_PREFIX: str = "/api/v1"
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000

    # Security & Auth
    SECRET_KEY: str = "civiclens-super-secret-development-key-change-in-production-32bytes"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # CORS
    CORS_ORIGINS: Union[str, List[str]] = (
        "http://localhost:3000,http://localhost:5173,"
        "http://localhost:8000,http://127.0.0.1:5173"
    )

    @property
    def cors_origins_list(self) -> List[str]:
        if isinstance(self.CORS_ORIGINS, list):
            return self.CORS_ORIGINS
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./civiclens.db"

    # Redis / In-Memory
    REDIS_URL: str = "redis://localhost:6379/0"
    USE_IN_MEMORY_CACHE: bool = True

    # Storage
    STORAGE_BACKEND: str = "local"
    LOCAL_STORAGE_PATH: str = "./storage/uploads"
    LOCAL_THUMBNAILS_PATH: str = "./storage/thumbnails"
    MAX_UPLOAD_SIZE_MB: int = 15
    ALLOWED_IMAGE_MIME_TYPES: str = "image/jpeg,image/png,image/webp,image/heic"

    @property
    def allowed_mime_types_list(self) -> List[str]:
        return [m.strip() for m in self.ALLOWED_IMAGE_MIME_TYPES.split(",") if m.strip()]

    # AI Engine
    AI_MODEL_DEVICE: str = "cpu"
    AI_CONFIDENCE_THRESHOLD: float = 0.65
    AI_DUPLICATE_SIMILARITY_THRESHOLD: float = 0.75
    AI_DUPLICATE_GEO_RADIUS_METERS: float = 150.0
    AI_SEVERITY_MODEL_PATH: str = "./ai/weights/severity_model.json"
    AI_CLASSIFIER_MODEL_PATH: str = "./ai/weights/issue_classifier.json"
    AI_VISION_MODEL_PATH: str = "./ai/weights/mobilenet_civic_v1.pt"

    # Priority Engine Weights
    PRIORITY_WEIGHT_SEVERITY: float = 0.35
    PRIORITY_WEIGHT_SAFETY_RISK: float = 0.25
    PRIORITY_WEIGHT_TRAFFIC_IMPACT: float = 0.15
    PRIORITY_WEIGHT_DUPLICATES: float = 0.15
    PRIORITY_WEIGHT_PERSISTENCE: float = 0.10

    # Civic Impact Scoring Weights (sum must equal 1.0)
    CIVIC_IMPACT_WEIGHT_SAFETY: float = 0.30       # safety → 0–30 pts
    CIVIC_IMPACT_WEIGHT_POPULATION: float = 0.25   # exposure → 0–25 pts
    CIVIC_IMPACT_WEIGHT_TRAFFIC: float = 0.20      # traffic → 0–20 pts
    CIVIC_IMPACT_WEIGHT_PERSISTENCE: float = 0.15  # days open → 0–15 pts
    CIVIC_IMPACT_WEIGHT_RECURRENCE: float = 0.10   # repeat count → 0–10 pts

    # Incident Clustering
    INCIDENT_CLUSTER_RADIUS_METERS: float = 300.0
    INCIDENT_CLUSTER_TIME_WINDOW_DAYS: int = 30
    INCIDENT_MIN_REPORTS_FOR_HOTSPOT: int = 3
    HOTSPOT_DETECTION_RADIUS_METERS: float = 500.0

    # Predictive Intelligence
    PREDICTION_MIN_HISTORY_DAYS: int = 30
    PREDICTION_RECURRENCE_THRESHOLD: int = 3
    PREDICTION_WINDOW_DAYS: int = 14

    # Spam / Fraud Detection
    SPAM_BURST_MAX_PER_HOUR: int = 5
    SPAM_IMAGE_HASH_MATCH_THRESHOLD: float = 0.95

    # Notifications
    FCM_SERVER_KEY: str = ""
    FIREBASE_CREDENTIALS_PATH: str = ""

    # SMTP
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "notifications@civiclens.local"
    SMTP_TLS: bool = True

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    COMPLAINT_SUBMISSION_LIMIT_PER_HOUR: int = 10

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # "json" or "console"

    # Observability
    ENABLE_METRICS: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
