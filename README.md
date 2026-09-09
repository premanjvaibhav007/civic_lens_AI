# CivicLens AI: AI-Powered Municipal Infrastructure Redressal Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-3776AB.svg?logo=python)](https://python.org)
[![Spring Boot](https://img.shields.io/badge/Spring_Boot-3.2.3-6DB33F.svg?logo=springboot)](https://spring.io)
[![Java](https://img.shields.io/badge/Java-17%20%7C%2021%20%7C%2023-ED8B00.svg?logo=openjdk)](https://openjdk.org)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg?logo=react)](https://reactjs.org)
[![Vite](https://img.shields.io/badge/Vite-5.0-646CFF.svg?logo=vite)](https://vitejs.dev)
[![Android](https://img.shields.io/badge/Android-Java%20%7C%20Kotlin-3DDC84.svg?logo=android)](https://developer.android.com)
[![Tests: Pytest](https://img.shields.io/badge/Tests-18%20Passing-brightgreen.svg)](https://pytest.org)

CivicLens AI is a production-ready, open-source, AI-powered civic grievance and infrastructure resolution platform. It bridges the gap between citizens, municipal field maintenance crews, and departmental administrators through automated multimodal defect triage, spatio-temporal duplicate detection, transparent SLA countdowns, and dual backend implementations in **Python (FastAPI)** and **Java (Spring Boot)** with a modern **React** web portal and **Java/Kotlin** Android mobile apps.

---

## 🏛️ System Architecture

```
                    ┌──────────────────────────────────────────────┐
                    │          CivicLens Client Ecosystem          │
                    ├──────────────────────┬───────────────────────┤
                    │ Android Citizen App  │ Authority Web Portal  │
                    │ (Kotlin/Compose/Room)│ (React/TS/Tailwind)   │
                    └──────────┬───────────┴───────────┬───────────┘
                               │                       │
                               ▼                       ▼
            ┌─────────────────────────────────────────────────────────────┐
            │                     FastAPI Gateway (v1)                    │
            │          - JWT Authentication & RBAC (Citizen/Admin)        │
            │          - MIME Inspection & EXIF Stripping                 │
            │          - Async State Machine & Audit Trails               │
            └──────────────┬───────────────────────────────┬──────────────┘
                           │                               │
                           ▼                               ▼
            ┌─────────────────────────────┐ ┌─────────────────────────────┐
            │   AI Triage & ML Engine     │ │   Honest Authority Adapter  │
            │ - Multimodal Issue Classif. │ │ - Internal Queue Routing    │
            │ - Spatio-Temporal Duplicates│ │ - Webhook / Email Fallback  │
            │ - Explainable Priority P1-4 │ │ - REST Smart City Bridges   │
            └──────────────┬──────────────┘ └──────────────┬──────────────┘
                           │                               │
                           └───────────────┬───────────────┘
                                           ▼
            ┌─────────────────────────────────────────────────────────────┐
            │                 PostgreSQL 16 / SQLite Engine               │
            │          (Complaints, Media, AI Telemetry, Audits)          │
            └─────────────────────────────────────────────────────────────┘
```

---

## ✨ Key Features

1. **AI-Powered Multimodal Triage**:
   - Classifies civic issues across 11 municipal categories (`POTHOLE`, `WATER_LEAKAGE`, `OPEN_MANHOLE`, `STREETLIGHT`, `GARBAGE`, etc.) using fused token resonance and visual features (texture variance, edge density, color histograms).
   - Calibrated severity estimation ($\pm 1$ grade accuracy of 90.40%).
2. **Spatio-Temporal Duplicate Clustering**:
   - Fuses Haversine distance, textual Jaccard similarity, and exponential temporal decay ($e^{-\Delta t / 30}$) to eliminate duplicate dispatch storms.
3. **Transparent Priority Engine ($P_1$–$P_4$)**:
   - 100% explainable priority ranking with dynamic SLA assignment (6h to 168h) and human-readable factor rationales.
4. **Authority Web Dashboard**:
   - Live KPI overview, department queues, Leaflet geographic maps, officer assignment modals, and Before vs After repair photo inspections.
5. **Native Android Citizen App**:
   - Built with Jetpack Compose & Material 3.
   - Offline-first Room DB with background syncing via `WorkManager`.
   - Real-time resolution timeline and bilingual localization (EN/HI).
6. **Reproducible Research Suite**:
   - Automated benchmark harness (`research/run_experiments.py`) evaluated over 250 ground-truth annotated cases.

---

## 🔬 Empirical Benchmark Highlights ($N=250$)

| Benchmark / Module | Metric | Result | Target Benchmark |
| :--- | :--- | :---: | :---: |
| **Classification Pipeline** | Mean Inference Latency | **0.33 ms** | $< 50 \text{ ms}$ |
| **Classification Pipeline** | Macro F1-Score | **0.6954** | Baseline Reference |
| **Spatio-Temporal Duplicate** | Clustering Precision | **100.0%** | $> 95.0\%$ |
| **Spatio-Temporal Duplicate** | Clustering Recall | **100.0%** | $> 95.0\%$ |
| **Severity Calibration** | $\pm 1$ Level Tolerance | **90.40%** | $> 85.0\%$ |
| **Priority Engine** | Explainability Coverage | **100.0%** | $100.0\%$ |

*See [`research/RESEARCH.md`](file:///c:/Users/hp/Desktop/PROJECTS/CivicLensAI/research/RESEARCH.md) for full statistical tables and confusion matrices.*

---

## 👥 Dual Portal Experience: Citizens & Municipal Authorities

CivicLens AI v2.0 provides an end-to-end civic accountability loop accessible directly from any web browser or mobile device:

### 1. 🏙️ Citizen Portal (`http://localhost:5173`)
- **Direct Web Complaint Filing**: Click `+ File Complaint` in the navigation header to report potholes, water leakages, garbage overflows, broken streetlights, or sanitation issues.
- **Auto-GPS Geolocation**: Detects exact latitude/longitude automatically via browser GPS or allows manual pin adjustment.
- **Multimodal Photo Upload**: Upload high-resolution scene photos with automatic preview and validation.
- **Transparent Live Authority Progress Tracking**:
  - 🟠 **Awaiting Dispatch**: Complaint logged and queued for departmental allocation.
  - 🟣 **AI Routed**: Multimodal classification assigned category, department, severity, and priority.
  - 🔵 **Authorities Working On-Site**: Field crew actively dispatched and repairing the infrastructure issue on-site.
  - 🟣 **Repaired - Review Proof**: Maintenance crew has uploaded official before/after resolution photos.
  - 🟢 **Verified Resolved**: Inspection passed, SLA fulfilled, and audit trail permanently recorded.
- **Personal Complaint Tracker**: Switch between **"My Filed Complaints"** and **"All Neighborhood Complaints"** in one click.

### 2. 🛡️ Authority Operations Dashboard
- **Live Triaging & Priority Queue**: View complaints ordered by explainable priority ($P_1$–$P_4$) with active SLA countdown clocks.
- **Geographic Heatmap**: Interactive Leaflet map with departmental clusters and incident zones.
- **One-Click Officer Dispatch**: Move issues from queued to `IN_PROGRESS` with assigned municipal personnel.
- **Resolution Proof Upload**: Upload after-repair photographic evidence to verify physical resolution before closure.
- **AI Copilot & Incident Command**: Ask natural-language operational questions and declare emergency weather/traffic alerts.

---

## 🔑 Demo Access Credentials

| Role | Email | Password | Pre-configured Access |
| :--- | :--- | :--- | :--- |
| **Citizen** | `citizen@civiclens.gov` | `Citizen@123456` | File grievances, track status live, view neighborhood feed |
| **Authority Admin** | `admin@civiclens.gov` | `Admin@123456` | Full departmental triage, officer dispatch, SLA tracking, analytics |

*(Click the quick **"Demo Citizen"** or **"Demo Authority"** preset buttons directly on the login modal for 1-click login!)*

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.11+
- Node.js 18+ / npm
- Android Studio Ladybug / Koala (for optional Android compilation)
- Docker & Docker Compose (optional for production containerization)

### 1a. Run Python FastAPI Backend & AI Engine (Port 8000)
```bash
# Activate virtual environment
.venv\Scripts\activate # On Windows
# source .venv/bin/activate # On Linux/macOS

# Initialize Database & Seed Demo Municipal Data
python backend/app/db/init_db.py

# Launch FastAPI Server
uvicorn backend.app.main:app --reload --port 8000
```
- Swagger API Docs: `http://localhost:8000/docs`
- Health Endpoint: `http://localhost:8000/health`

### 1b. Run Java Spring Boot Backend (Port 8080)
```bash
cd backend-springboot

# Run with Maven or Gradle
mvn spring-boot:run
```
- Spring Boot REST API: `http://localhost:8080/api/v1/complaints`
- Health Check: `http://localhost:8080/health`
- Embedded H2 Console: `http://localhost:8080/h2-console`

### 2. Run Web Portal (Citizen & Authority)
```bash
cd web
npm install
npm run dev
```
- Web Portal: `http://localhost:5173`

### 3. Run Automated Tests & Experiments
```bash
# Run Backend Test Suite (18 unit & integration tests)
pytest -v

# Run Full Research Experiment Benchmark Suite
python research/run_experiments.py
```

### 4. 1-Click Cloud Deployment (Render Blueprint)
This repository includes a production-ready `render.yaml` blueprint:
1. Fork or push this repository to GitHub.
2. Go to [Render Dashboard](https://dashboard.render.com/) -> **New** -> **Blueprint**.
3. Connect your repository (`civic_lens_AI`).
4. Render will automatically spin up:
   - **PostgreSQL 16** managed database
   - **FastAPI Backend** web service (Python 3.11) with health checks
   - **React/Vite Frontend** static site with automatic API reverse proxying

### 5. Deploy Frontend on Vercel (Recommended for Global CDN)
You can deploy the Citizen & Authority Web Portal to **Vercel** in 2 minutes:
1. Go to [Vercel Dashboard](https://vercel.com/new) -> **Add New Project**.
2. Import your GitHub repository (`civic_lens_AI`).
3. Set **Root Directory** to `web` (or leave default root; both are supported via `vercel.json`).
4. In **Environment Variables**, add:
   - `VITE_BACKEND_URL`: Your deployed FastAPI backend URL (e.g. `https://civiclens-ai-backend.onrender.com`).
5. Click **Deploy**!
   - Vercel will build the frontend with Vite and provide a production domain with instant global edge caching and free SSL.
   - The FastAPI backend includes built-in CORS regex support for all `*.vercel.app` preview and production domains.

### 6. Run with Docker Compose
```bash
cd infrastructure
docker-compose up --build -d
```

---

## 📁 Repository Structure

```
CivicLensAI/
├── ai/                     # Multimodal Classification & Priority Engine
│   └── models/             # classifier, severity, duplicate_detector, priority_engine
├── backend/                # FastAPI Application & Async SQLAlchemy 2.0
│   ├── app/                # api, core, db, models, schemas, services, adapters
│   └── tests/              # Pytest test suite
├── web/                    # React 18 / TypeScript / Tailwind Authority Dashboard
├── android/                # Native Android Citizen App (Kotlin, Compose, Room, WorkManager)
├── research/               # Benchmark Dataset, Experiment Harness, and Findings
│   ├── data/               # benchmark_dataset.json (250 annotated items)
│   ├── results/            # empirical JSON & CSV experiment outputs
│   └── run_experiments.py  # Automated benchmark evaluation runner
├── infrastructure/         # Multi-stage Dockerfiles, docker-compose, Nginx confs
└── docs/                   # Architecture, API, Database, Play Store, Security & Privacy
```

---

## 📜 Documentation Index
- [Architecture Design](file:///c:/Users/hp/Desktop/PROJECTS/CivicLensAI/docs/ARCHITECTURE.md)
- [REST API Reference](file:///c:/Users/hp/Desktop/PROJECTS/CivicLensAI/docs/API.md)
- [Database Schema & ERD](file:///c:/Users/hp/Desktop/PROJECTS/CivicLensAI/docs/DATABASE.md)
- [AI & ML Models](file:///c:/Users/hp/Desktop/PROJECTS/CivicLensAI/docs/AI_MODELS.md)
- [Deployment Guide](file:///c:/Users/hp/Desktop/PROJECTS/CivicLensAI/docs/DEPLOYMENT.md)
- [Research Methodology](file:///c:/Users/hp/Desktop/PROJECTS/CivicLensAI/research/RESEARCH.md)
- [Google Play Release & Privacy](file:///c:/Users/hp/Desktop/PROJECTS/CivicLensAI/docs/PLAYSTORE.md)

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
