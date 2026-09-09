from fastapi import APIRouter
from backend.app.api.v1.endpoints import (
    auth, complaints, admin, analytics, storage, notifications,
    incidents, assets, maps, predictions, copilot
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(complaints.router)
api_router.include_router(admin.router)
api_router.include_router(analytics.router)
api_router.include_router(storage.router)
api_router.include_router(notifications.router)
# Stage 3+ new routers
api_router.include_router(incidents.router)
api_router.include_router(assets.router)
api_router.include_router(maps.router)
api_router.include_router(predictions.router)
api_router.include_router(copilot.router)
