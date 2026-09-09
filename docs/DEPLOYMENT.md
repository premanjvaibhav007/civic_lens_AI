# CivicLens AI — Deployment & Operations Guide

## 1. Quick Local Development Setup

### 1.1 Backend Setup
```bash
# 1. Clone repository and navigate to root
cd CivicLensAI

# 2. Activate Python virtual environment
.venv\Scripts\activate # On Windows
source .venv/bin/activate # On Linux/macOS

# 3. Install dependencies
pip install -r backend/requirements.txt

# 4. Initialize database and seed sample municipal data
python backend/app/db/init_db.py

# 5. Start FastAPI development server
uvicorn backend.app.main:app --reload --port 8000
```
- API Documentation: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

### 1.2 Web Dashboard Setup
```bash
cd web
npm install
npm run dev
```
- Dashboard URL: `http://localhost:5173`
- Default Admin Login: `admin@civiclens.gov` / `Admin@123456`

---

## 2. Docker Compose Production Deployment

To run the complete production stack (PostgreSQL 16, Redis 7, Backend API, Web Dashboard with Nginx):

```bash
cd infrastructure
docker-compose up --build -d
```

### Checking Container Health:
```bash
docker-compose ps
docker-compose logs -f backend
```

---

## 3. Environment Variables Reference (`.env`)

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `DATABASE_URL` | `sqlite+aiosqlite:///./civiclens.db` | SQLAlchemy connection URI |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis caching & async queue |
| `SECRET_KEY` | `your_jwt_secret_key_here` | 256-bit cryptographic key |
| `ENVIRONMENT` | `development` / `production` | Environment mode |
| `STORAGE_BACKEND` | `local` / `s3` / `gcs` | Media storage provider |
| `STORAGE_LOCAL_ROOT` | `./storage` | Directory for uploads |
