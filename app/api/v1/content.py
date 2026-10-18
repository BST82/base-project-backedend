import os
import uuid
import aiofiles
from typing import Dict, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_active_admin
from app.models.site_content import SiteContent
from app.schemas.site_content import (
    SiteContentResponse,
    SiteContentUpdate,
    SiteContentBulkUpdate,
)

router = APIRouter(prefix="/content", tags=["CMS Content"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("", response_model=Dict[str, str])
async def get_all_site_content(db: AsyncSession = Depends(get_db)):
    """Public endpoint: returns all CMS key-values as a flat map for direct frontend binding."""
    result = await db.execute(select(SiteContent))
    contents = result.scalars().all()
    return {item.key: item.value for item in contents}


@router.get("/detailed", response_model=List[SiteContentResponse])
async def get_detailed_site_content(db: AsyncSession = Depends(get_db)):
    """Admin endpoint: returns full metadata for CMS content management."""
    result = await db.execute(select(SiteContent).order_by(SiteContent.category, SiteContent.key))
    return result.scalars().all()


@router.put("/bulk", response_model=Dict[str, str])
async def update_bulk_site_content(
    payload: SiteContentBulkUpdate,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_active_admin)
):
    """Admin endpoint: bulk update dynamic CMS text, logo URL, or banners without redeploy."""
    for key, val in payload.contents.items():
        result = await db.execute(select(SiteContent).where(SiteContent.key == key))
        item = result.scalar_one_or_none()
        if item:
            item.value = val
        else:
            new_item = SiteContent(key=key, value=val, category="custom")
            db.add(new_item)
    
    await db.commit()
    
    # Return fresh map
    all_res = await db.execute(select(SiteContent))
    return {c.key: c.value for c in all_res.scalars().all()}


@router.put("/{key}", response_model=SiteContentResponse)
async def update_single_content(
    key: str,
    update_in: SiteContentUpdate,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_active_admin)
):
    result = await db.execute(select(SiteContent).where(SiteContent.key == key))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Content key '{key}' not found")
    
    item.value = update_in.value
    if update_in.description:
        item.description = update_in.description
    
    await db.commit()
    await db.refresh(item)
    return item


@router.post("/upload-asset")
async def upload_asset(
    file: UploadFile = File(...),
    admin=Depends(get_current_active_admin)
):
    """Admin endpoint: upload logo, banner or dish image."""
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png", ".webp", ".svg"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported image format")
    
    filename = f"{uuid.uuid4().hex}{ext}"
    content_bytes = await file.read()

    backend_base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    dirs_to_save = [
        UPLOAD_DIR,
        os.path.abspath(os.path.join(backend_base, "backend", "uploads")),
        os.path.abspath(os.path.join(backend_base, "backend", "app", "uploads")),
        os.path.abspath(os.path.join(backend_base, "frontend", "public", "uploads")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "uploads")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "uploads")),
    ]
    
    for d in set(dirs_to_save):
        try:
            os.makedirs(d, exist_ok=True)
            async with aiofiles.open(os.path.join(d, filename), "wb") as out_file:
                await out_file.write(content_bytes)
        except Exception:
            pass

    return {"url": f"/uploads/{filename}", "filename": filename}

