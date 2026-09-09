import os
import io
import uuid
import hashlib
from typing import Optional, Tuple
from PIL import Image, ImageOps
from fastapi import UploadFile, HTTPException, status
from backend.app.core.config import settings

class StorageService:
    def __init__(self):
        self.upload_dir = os.path.abspath(settings.LOCAL_STORAGE_PATH)
        self.thumbnail_dir = os.path.abspath(settings.LOCAL_THUMBNAILS_PATH)
        os.makedirs(self.upload_dir, exist_ok=True)
        os.makedirs(self.thumbnail_dir, exist_ok=True)

    def validate_image_file(self, content_type: str, file_size: int):
        if content_type not in settings.allowed_mime_types_list:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format '{content_type}'. Allowed: {settings.allowed_mime_types_list}"
            )
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if file_size > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds maximum allowed limit of {settings.MAX_UPLOAD_SIZE_MB}MB"
            )

    async def save_upload_file(self, file: UploadFile) -> Tuple[str, Optional[str], int, str, str]:
        contents = await file.read()
        file_size = len(contents)
        self.validate_image_file(file.content_type, file_size)

        # Calculate SHA256 checksum
        image_hash = hashlib.sha256(contents).hexdigest()

        # Generate unique filename
        file_ext = self._get_extension(file.filename or "image.jpg", file.content_type)
        file_id = str(uuid.uuid4())
        filename = f"{file_id}{file_ext}"
        filepath = os.path.join(self.upload_dir, filename)

        # Process image: strip EXIF, normalize orientation, optimize
        try:
            with Image.open(io.BytesIO(contents)) as img:
                # Transpose according to EXIF orientation, then strip EXIF
                img = ImageOps.exif_transpose(img)
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                img.save(filepath, format="JPEG", quality=85, optimize=True)
        except Exception:
            # Fallback if image processing fails
            with open(filepath, "wb") as f:
                f.write(contents)

        # Generate thumbnail
        thumb_filename = f"thumb_{file_id}.jpg"
        thumb_filepath = os.path.join(self.thumbnail_dir, thumb_filename)
        try:
            with Image.open(filepath) as img:
                img.thumbnail((320, 320), Image.Resampling.LANCZOS)
                img.save(thumb_filepath, format="JPEG", quality=80)
            thumbnail_url = f"/api/v1/storage/thumbnails/{thumb_filename}"
        except Exception:
            thumbnail_url = None

        image_url = f"/api/v1/storage/images/{filename}"
        return image_url, thumbnail_url, file_size, file.content_type, image_hash

    def save_bytes_image(self, contents: bytes, filename_hint: str = "capture.jpg") -> Tuple[str, Optional[str], int, str, str]:
        file_size = len(contents)
        image_hash = hashlib.sha256(contents).hexdigest()
        file_id = str(uuid.uuid4())
        filename = f"{file_id}.jpg"
        filepath = os.path.join(self.upload_dir, filename)

        try:
            with Image.open(io.BytesIO(contents)) as img:
                img = ImageOps.exif_transpose(img)
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                img.save(filepath, format="JPEG", quality=85, optimize=True)
        except Exception:
            with open(filepath, "wb") as f:
                f.write(contents)

        thumb_filename = f"thumb_{file_id}.jpg"
        thumb_filepath = os.path.join(self.thumbnail_dir, thumb_filename)
        try:
            with Image.open(filepath) as img:
                img.thumbnail((320, 320), Image.Resampling.LANCZOS)
                img.save(thumb_filepath, format="JPEG", quality=80)
            thumbnail_url = f"/api/v1/storage/thumbnails/{thumb_filename}"
        except Exception:
            thumbnail_url = None

        image_url = f"/api/v1/storage/images/{filename}"
        return image_url, thumbnail_url, file_size, "image/jpeg", image_hash

    def _get_extension(self, filename: str, mime_type: str) -> str:
        _, ext = os.path.splitext(filename)
        if ext:
            return ext.lower()
        if "png" in mime_type:
            return ".png"
        if "webp" in mime_type:
            return ".webp"
        return ".jpg"

storage_service = StorageService()
