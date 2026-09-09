# CivicLens AI — System Architecture & Design Specification

## 1. High-Level Architectural Overview

CivicLens AI is designed as a decoupled, event-aware municipal grievance redressal platform with strict separation of concerns:

```
[ Citizen Native Android App ]      [ Municipal Authority Web Dashboard ]
(Kotlin, Compose, Room, WorkMgr)    (React, TypeScript, Tailwind, Leaflet)
               │                                      │
               └───────────────┬──────────────────────┘
                               │ HTTPS / JSON REST API
                               ▼
            ┌─────────────────────────────────────────┐
            │       FastAPI Gateway (Uvicorn)         │
            │  - JWT RBAC (Citizen / Officer / Admin) │
            │  - Pydantic v2 Contract Validation      │
            │  - CORS & Security Header Middleware    │
            └────────────────────┬────────────────────┘
                                 │
           ┌─────────────────────┼─────────────────────┐
           ▼                     ▼                     ▼
┌────────────────────┐ ┌────────────────────┐ ┌────────────────────┐
│ Complaint Service  │ │ AI Triage Engine   │ │ Authority Adapter  │
│ - Finite State M/C │ │ - Multimodal Model │ │ - Routing Engine   │
│ - SLA Clock Mgr    │ │ - Spatio-Temporal  │ │ - Webhook / Email  │
│ - Audit Logger     │ │ - Explainable P1-4 │ │ - REST Integration │
└──────────┬─────────┘ └─────────┬──────────┘ └─────────┬──────────┘
           │                     │                      │
           ▼                     ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│              Async SQLAlchemy 2.0 Engine Layer                  │
│       (PostgreSQL in Production / aiosqlite for Local Dev)      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Core Subsystems

### 2.1 Backend Core & API Layer (`/backend`)
- **Framework**: Python 3.11+ / FastAPI with fully asynchronous endpoint handlers.
- **ORM & Data Layer**: SQLAlchemy 2.0 in `async` mode using `asyncpg` (PostgreSQL) or `aiosqlite` (SQLite).
- **Authentication**: JWT tokens (15m access / 7d refresh) using `passlib[bcrypt]` and `python-jose`.
- **Media Pipeline**: Asynchronous image resizing, thumbnailing, and EXIF sanitization using `Pillow`.

### 2.2 Artificial Intelligence & Triage Engine (`/ai`)
- **Multimodal Classification**: Fuses keyword token heuristics with deterministic visual features (edge density, color temperature, variance) for zero-latency categorization.
- **Spatio-Temporal Duplicate Clustering**: Evaluates Haversine distance, textual Jaccard similarity, and exponential temporal decay ($e^{-\Delta t / 30}$) to prevent duplicate ticket storms.
- **Explainable Multi-Factor Priority**: Assigns $P_1$ to $P_4$ urgency with human-readable rationales based on safety hazard profiles, traffic impact, and SLA deadlines.

### 2.3 Municipal Authority Web Dashboard (`/web`)
- **Tech Stack**: React 18, TypeScript, Tailwind CSS, Lucide React, TanStack Query, Leaflet Maps.
- **Features**:
  - Live Overview metrics (Total Complaints, Resolved %, Avg Resolution Time, Active SLA Breaches).
  - Departmental Queue with dynamic filtering, bulk actions, and status transitions.
  - Interactive Leaflet Map with categorical pin colors and clustering.
  - Granular Complaint Detail modal with image comparison (Before vs Resolution Proof), audit trails, and officer assignment.
  - Administrative Config panel for SLA thresholds and priority weight adjustment.

### 2.4 Citizen Native Android Application (`/android`)
- **Tech Stack**: Kotlin, Jetpack Compose, Material 3, Android Architecture Components (MVVM), Room DB, Retrofit 2, OkHttp 3, WorkManager.
- **Features**:
  - Smart issue reporting with live camera preview, category selector, GPS geotagging, and voice/text input.
  - Offline-first architecture: drafts saved to local Room SQLite DB and synced automatically via `SyncDraftsWorker`.
  - Grievance tracking with real-time progress timeline and resolution photo verification.
  - Bilingual localization (English & Hindi).

### 2.5 Authority Integration Layer (`/backend/app/adapters`)
- Built on an extensible `BaseAuthorityAdapter` pattern.
- Implements:
  - `DashboardRoutingAdapter`: Native internal routing to municipal officer queues.
  - `WebhookAdapter`: Dispatches signed JSON payloads to municipal external endpoints.
  - `EmailAdapter`: Generates official notification dispatches to nodal department heads.
  - `RESTAPIAdapter`: Pluggable HTTP REST client for official smart city grievance systems.
