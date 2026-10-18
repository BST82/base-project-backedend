from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_active_admin
from app.models.banner_slide import BannerSlide
from app.schemas.banner_slide import BannerSlideCreate, BannerSlideUpdate, BannerSlideResponse

router = APIRouter(prefix="/banner-slides", tags=["Hero Banner Sliders CMS"])


@router.get("", response_model=List[BannerSlideResponse])
async def list_active_slides(db: AsyncSession = Depends(get_db)):
    """Public endpoint: returns all active banner slides ordered by display_order."""
    result = await db.execute(
        select(BannerSlide).where(BannerSlide.is_active == True).order_by(BannerSlide.display_order, BannerSlide.id)
    )
    return result.scalars().all()


@router.get("/admin/all", response_model=List[BannerSlideResponse])
async def list_all_slides_admin(
    db: AsyncSession = Depends(get_db),
    admin = Depends(get_current_active_admin)
):
    """Admin endpoint: returns all banner slides."""
    result = await db.execute(select(BannerSlide).order_by(BannerSlide.display_order, BannerSlide.id))
    return result.scalars().all()


@router.post("", response_model=BannerSlideResponse, status_code=status.HTTP_201_CREATED)
async def create_slide(
    slide_in: BannerSlideCreate,
    db: AsyncSession = Depends(get_db),
    admin = Depends(get_current_active_admin)
):
    slide = BannerSlide(**slide_in.model_dump())
    db.add(slide)
    await db.commit()
    await db.refresh(slide)
    return slide


@router.put("/{slide_id}", response_model=BannerSlideResponse)
async def update_slide(
    slide_id: int,
    slide_in: BannerSlideUpdate,
    db: AsyncSession = Depends(get_db),
    admin = Depends(get_current_active_admin)
):
    result = await db.execute(select(BannerSlide).where(BannerSlide.id == slide_id))
    slide = result.scalar_one_or_none()
    if not slide:
        raise HTTPException(status_code=404, detail="Banner slide not found")

    for field, val in slide_in.model_dump(exclude_unset=True).items():
        setattr(slide, field, val)

    await db.commit()
    await db.refresh(slide)
    return slide


@router.delete("/{slide_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_slide(
    slide_id: int,
    db: AsyncSession = Depends(get_db),
    admin = Depends(get_current_active_admin)
):
    result = await db.execute(select(BannerSlide).where(BannerSlide.id == slide_id))
    slide = result.scalar_one_or_none()
    if not slide:
        raise HTTPException(status_code=404, detail="Banner slide not found")

    await db.delete(slide)
    await db.commit()
