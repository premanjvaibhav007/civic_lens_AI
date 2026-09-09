# CivicLens AI — Technical Debt & Architectural Decisions Register

**Version:** 2.0.0  
**Updated:** 2026-09-09  
**Status:** Active  

---

## 1. Executive Summary

This document catalogues intentional architectural trade-offs, temporary bridges, known edge cases, and future migration milestones for the CivicLens AI platform as it upgrades to Version 2.0.

---

## 2. Architecture & Data Storage

### TD-01: Development SQLite vs. Production PostgreSQL + PostGIS
- **Current State:** Local development defaults to `sqlite+aiosqlite:///./civiclens.db` for zero-configuration developer bootstrapping.
- **Limitation:** SQLite lacks native spatial indices (`R-Tree` requires special SQLite compile flags) and doesn't support concurrent write connections with high worker counts.
- **Production Path:** In production (`ENVIRONMENT=production`), use PostgreSQL with PostGIS extension. Spatial distance queries currently utilize the Haversine formula implemented in pure Python/SQL math in `ai/models/duplicate_detector.py` and `incident_service.py`. This ensures identical behavior across both SQLite and PostgreSQL.
- **Action Required for Scale:** Enable `ST_DWithin` and `ST_DistanceSphere` once PostgreSQL PostGIS is provisioned in Kubernetes/RDS.

### TD-02: Synchronous Image Processing in Dev vs. Distributed Celery/Redis
- **Current State:** AI inferences and visual diff analysis run asynchronously via FastAPI background tasks and async worker functions.
- **Limitation:** Heavy batch ML operations (e.g., re-clustering 100,000 complaints) in-process can elevate API latency if single-worker CPU is saturated.
- **Mitigation:** In-memory caching and non-blocking IO keep the HTTP thread free.
- **Future Milestone:** Add a dedicated Celery / RQ worker container for offline nightly hotspot recalibration and ML model retraining.

---

## 3. AI & ML Pipeline

### TD-03: Multimodal Vision Model Fallback Architecture
- **Current State:** The image classifier uses a hybrid progressive design:
  1. If `ai/weights/mobilenet_civic_v1.pt` and PyTorch are present, it evaluates visual features.
  2. If absent or during lightweight test runs, it defaults safely to keyword extraction, metadata analysis, and rule-based heuristic classification.
- **Confidence Tiers:** Low confidence predictions (`confidence < 0.65`) flag `requires_manual_verification = True` and set `AIStatus.LOW_CONFIDENCE`. No unverified automated decisions are enacted.
- **Future Improvement:** Deploy Triton Inference Server or TorchServe sidecar container in production for GPU-accelerated batch image inference.

### TD-04: Predictive Intelligence Data Threshold
- **Current State:** The infrastructure failure risk predictor requires at least `PREDICTION_MIN_HISTORY_DAYS` (30 days) of real geographic complaint density.
- **Guaranteed Policy:** If fewer than 30 days of data are recorded in a ward, the API explicitly returns `"status": "INSUFFICIENT_DATA"` with a descriptive note. **Fake or hallucinated risk forecasts are strictly prohibited.**

---

## 4. API & Security

### TD-05: Rate Limiting
- **Current State:** Default rate limiting is enforced via middleware (`RATE_LIMIT_PER_MINUTE = 60`) and IP burst checking in `spam_detection_service.py`.
- **Future Improvement:** Centralized Redis-backed token bucket filter for multi-instance horizontal scaling.

### TD-06: RBAC & Audit Trails
- **Current State:** Strict role enforcement on all officer and admin endpoints via `require_officer` and `require_admin`. Every status update produces an immutable row in `ComplaintStatusHistory` or `IncidentStatusHistory`.

---

## 5. Summary Matrix

| ID | Domain | Impact | Current Mitigation | Resolution Target |
|----|--------|--------|--------------------|-------------------|
| TD-01 | DB | Med | Haversine pure-math spatial queries | PostGIS migration in Prod |
| TD-02 | Async | Low | Async background tasks & caching | Celery distributed worker |
| TD-03 | Vision AI | Low | Deterministic fallback + confidence tiers | Cloud GPU inference pod |
| TD-04 | Predictions | None | Explicit INSUFFICIENT_DATA reporting | Live data accumulation |
| TD-05 | Rate Limit | Low | In-memory burst counter | Redis token-bucket cluster |
