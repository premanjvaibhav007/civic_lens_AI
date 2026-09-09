import os
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from backend.app.core.config import settings

router = APIRouter(prefix="/storage", tags=["Media & Storage"])

@router.get("/images/{filename}")
async def get_image(filename: str):
    # Sanitize filename
    safe_filename = os.path.basename(filename)
    filepath = os.path.join(os.path.abspath(settings.LOCAL_STORAGE_PATH), safe_filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    return FileResponse(filepath)

@router.get("/thumbnails/{filename}")
async def get_thumbnail(filename: str):
    safe_filename = os.path.basename(filename)
    filepath = os.path.join(os.path.abspath(settings.LOCAL_THUMBNAILS_PATH), safe_filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thumbnail not found")
    return FileResponse(filepath)
