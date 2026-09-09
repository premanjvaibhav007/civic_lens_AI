# CivicLens AI: AI-Powered Municipal Infrastructure Redressal Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg?logo=react)](https://reactjs.org)
[![Kotlin](https://img.shields.io/badge/Kotlin-2.0.0-7F52FF.svg?logo=kotlin)](https://kotlinlang.org)
[![Jetpack Compose](https://img.shields.io/badge/Jetpack_Compose-2024.06.00-4285F4.svg?logo=android)](https://developer.android.com/jetpack/compose)
[![Tests: Pytest](https://img.shields.io/badge/Tests-Passing-brightgreen.svg)](https://pytest.org)

CivicLens AI is a production-ready, open-source, AI-powered civic grievance and infrastructure resolution platform. It bridges the gap between citizens, municipal field maintenance crews, and departmental administrators through automated multimodal defect triage, spatio-temporal duplicate detection, transparent SLA countdowns, and offline-first mobile synchronization.

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

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.11+
- Node.js 18+ / npm
- Android Studio Ladybug / Koala (for Android compilation)
- Docker & Docker Compose (optional for production containerization)

### 1. Run Backend & Initialize Database
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

### 2. Run Authority Web Dashboard
```bash
cd web
npm install
npm run dev
```
- Web Portal: `http://localhost:5173`
- Demo Admin Credentials: `admin@civiclens.gov` / `Admin@123456`

### 3. Run Automated Tests & Experiments
```bash
# Run Backend Test Suite
pytest -v

# Run Full Research Experiment Benchmark Suite
python research/run_experiments.py
```

### 4. Run with Docker Compose
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
