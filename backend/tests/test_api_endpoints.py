import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.db.init_db import init_db

@pytest_asyncio.fixture(scope="module", autouse=True)
async def setup_database():
    await init_db()

@pytest.mark.asyncio
async def test_health_check():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"

@pytest.mark.asyncio
async def test_metrics_and_readiness():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        ready_resp = await client.get("/ready")
        assert ready_resp.status_code == 200
        assert ready_resp.json()["status"] == "ready"

        metrics_resp = await client.get("/metrics")
        assert metrics_resp.status_code == 200
        assert "http_request_duration_seconds" in metrics_resp.text or "http_requests_total" in metrics_resp.text

@pytest.mark.asyncio
async def test_auth_flow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Login admin
        login_resp = await client.post("/api/v1/auth/login", json={
            "email": "admin@civiclens.gov",
            "password": "Admin@123456"
        })
        assert login_resp.status_code == 200
        auth_data = login_resp.json()["data"]
        assert auth_data["access_token"] is not None
        token = auth_data["access_token"]

        # Get me profile
        me_resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me_resp.status_code == 200
        assert me_resp.json()["data"]["role"] == "ADMIN"

@pytest.mark.asyncio
async def test_complaints_list():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login_resp = await client.post("/api/v1/auth/login", json={
            "email": "admin@civiclens.gov",
            "password": "Admin@123456"
        })
        token = login_resp.json()["data"]["access_token"]

        list_resp = await client.get("/api/v1/complaints", headers={"Authorization": f"Bearer {token}"})
        assert list_resp.status_code == 200
        data = list_resp.json()["data"]
        assert data["total"] >= 1
        assert len(data["items"]) >= 1

@pytest.mark.asyncio
async def test_nearby_complaints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/complaints/nearby?latitude=28.6328&longitude=77.2197&radius_meters=5000")
        assert resp.status_code == 200
        assert resp.json()["success"] is True

@pytest.mark.asyncio
async def test_analytics_dashboard():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login_resp = await client.post("/api/v1/auth/login", json={
            "email": "admin@civiclens.gov",
            "password": "Admin@123456"
        })
        token = login_resp.json()["data"]["access_token"]

        resp = await client.get("/api/v1/analytics/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        dash_data = resp.json()["data"]
        assert "metrics" in dash_data
        assert "category_distribution" in dash_data
        assert "geo_hotspots" in dash_data


@pytest.mark.asyncio
async def test_incidents_list_and_geojson():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login_resp = await client.post("/api/v1/auth/login", json={
            "email": "admin@civiclens.gov",
            "password": "Admin@123456"
        })
        token = login_resp.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.get("/api/v1/incidents", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["success"] is True

        geo_resp = await client.get("/api/v1/incidents/geojson", headers=headers)
        assert geo_resp.status_code == 200
        assert geo_resp.json()["type"] == "FeatureCollection"


@pytest.mark.asyncio
async def test_assets_lifecycle():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login_resp = await client.post("/api/v1/auth/login", json={
            "email": "admin@civiclens.gov",
            "password": "Admin@123456"
        })
        token = login_resp.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # List
        resp = await client.get("/api/v1/assets", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["success"] is True

        # GeoJSON
        geo_resp = await client.get("/api/v1/assets/geojson", headers=headers)
        assert geo_resp.status_code == 200
        assert geo_resp.json()["type"] == "FeatureCollection"

        # Create
        import uuid
        unique_code = f"RD-DEL-{uuid.uuid4().hex[:6].upper()}"
        create_resp = await client.post("/api/v1/assets", headers=headers, json={
            "asset_code": unique_code,
            "asset_type": "ROAD",
            "name": "Connaught Place Inner Circle Arterial",
            "latitude": 28.6328,
            "longitude": 77.2197,
            "health_score": 85.0
        })
        assert create_resp.status_code in (200, 201)
        created_asset = create_resp.json()["data"]
        asset_id = created_asset["id"]

        # Detail
        detail_resp = await client.get(f"/api/v1/assets/{asset_id}", headers=headers)
        assert detail_resp.status_code == 200
        assert detail_resp.json()["data"]["asset_code"] == unique_code

        # Update Health
        health_resp = await client.patch(f"/api/v1/assets/{asset_id}/health", headers=headers, json={
            "health_score": 60.0,
            "notes": "Routine pothole patching completed"
        })
        assert health_resp.status_code == 200
        assert health_resp.json()["data"]["health_score"] == 60.0
        assert health_resp.json()["data"]["risk_level"] == "MEDIUM"


@pytest.mark.asyncio
async def test_predictions_status_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login_resp = await client.post("/api/v1/auth/login", json={
            "email": "admin@civiclens.gov",
            "password": "Admin@123456"
        })
        token = login_resp.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.get("/api/v1/predictions/status", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "has_sufficient_data" in data
        assert "minimum_required_days" in data
        assert data["minimum_required_days"] == 30


@pytest.mark.asyncio
async def test_copilot_query_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login_resp = await client.post("/api/v1/auth/login", json={
            "email": "admin@civiclens.gov",
            "password": "Admin@123456"
        })
        token = login_resp.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.post("/api/v1/copilot/query", headers=headers, json={
            "query": "Show all critical open potholes"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "answer" in data
        assert "intent" in data
        assert "source_records" in data
