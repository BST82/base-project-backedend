from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_optional_current_user, get_current_active_admin
from app.models.review import Review
from app.models.user import User
from app.schemas.review import (
    ReviewCreate,
    ReviewResponse,
    ReviewModerationUpdate,
)

router = APIRouter(prefix="/reviews", tags=["Customer Reviews"])


@router.get("", response_model=List[ReviewResponse])
async def list_approved_reviews(db: AsyncSession = Depends(get_db)):
    """Public endpoint: displays all verified and approved customer reviews."""
    result = await db.execute(
        select(Review).where(Review.is_approved == True).order_by(Review.created_at.desc())
    )
    return result.scalars().all()


@router.post("", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def submit_review(
    review_in: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Public / customer endpoint: submits review into the admin moderation queue."""
    review = Review(
        user_id=current_user.id if current_user else None,
        customer_name=review_in.customer_name,
        rating=review_in.rating,
        comment=review_in.comment,
        is_approved=False  # Requires admin approval before appearing publicly
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)
    return review


@router.get("/all", response_model=List[ReviewResponse])
async def list_all_reviews_for_admin(
    is_approved: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_active_admin)
):
    """Admin moderation view: lists all reviews filtered by approval status."""
    query = select(Review)
    if is_approved is not None:
        query = query.where(Review.is_approved == is_approved)
    
    result = await db.execute(query.order_by(Review.created_at.desc()))
    return result.scalars().all()


@router.patch("/{review_id}/moderate", response_model=ReviewResponse)
async def moderate_review(
    review_id: int,
    mod_in: ReviewModerationUpdate,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_active_admin)
):
    """Admin endpoint: approve or reject a customer review."""
    result = await db.execute(select(Review).where(Review.id == review_id))
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    review.is_approved = mod_in.is_approved
    await db.commit()
    await db.refresh(review)
    return review


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_active_admin)
):
    result = await db.execute(select(Review).where(Review.id == review_id))
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    await db.delete(review)
    await db.commit()
