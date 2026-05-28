import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException

from app.auth import get_current_cashier

UPLOADS_DIR = Path(__file__).parent.parent.parent / "uploads"
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_SIZE_MB = 5

router = APIRouter(prefix="/api/uploads", tags=["uploads"])


@router.post("/photo")
async def upload_photo(file: UploadFile = File(...), _=Depends(get_current_cashier)):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, WebP and GIF images are allowed")

    contents = await file.read()
    if len(contents) > MAX_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File too large (max {MAX_SIZE_MB}MB)")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "jpg"
    filename = f"{uuid.uuid4().hex}.{ext}"
    (UPLOADS_DIR / filename).write_bytes(contents)

    return {"url": f"/uploads/{filename}"}
