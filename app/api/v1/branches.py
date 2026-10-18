from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_active_admin
from app.models.branch import Branch
from app.schemas.branch import BranchCreate, BranchUpdate, BranchResponse

router = APIRouter(prefix="/branches", tags=["Multi-Branch Store Locator"])


@router.get("", response_model=List[BranchResponse])
async def list_branches(
    city: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Public endpoint: returns active branches, filterable by city."""
    query = select(Branch).where(Branch.is_active == True)
    if city and city.lower() != "all":
        query = query.where(func.lower(Branch.city) == city.lower())
    
    result = await db.execute(query.order_by(Branch.city, Branch.name))
    return result.scalars().all()


@router.get("/cities", response_model=List[str])
async def list_distinct_cities(db: AsyncSession = Depends(get_db)):
    """Returns list of distinct cities having active restaurant branches."""
    result = await db.execute(
        select(Branch.city).where(Branch.is_active == True).distinct().order_by(Branch.city)
    )
    return [c for c in result.scalars().all() if c]


@router.get("/admin/all", response_model=List[BranchResponse])
async def list_all_branches_admin(
    db: AsyncSession = Depends(get_db),
    admin = Depends(get_current_active_admin)
):
    """Admin endpoint: lists all branches."""
    result = await db.execute(select(Branch).order_by(Branch.city, Branch.name))
    return result.scalars().all()


@router.post("", response_model=BranchResponse, status_code=status.HTTP_201_CREATED)
async def create_branch(
    branch_in: BranchCreate,
    db: AsyncSession = Depends(get_db),
    admin = Depends(get_current_active_admin)
):
    data = branch_in.model_dump()
    if data.get("operating_hours") and not data.get("opening_hours"):
        data["opening_hours"] = data.pop("operating_hours")
    valid_cols = {"name", "city", "address", "phone", "email", "latitude", "longitude", "opening_hours", "image_url", "is_active"}
    clean_data = {k: v for k, v in data.items() if k in valid_cols}
    branch = Branch(**clean_data)
    db.add(branch)
    await db.commit()
    await db.refresh(branch)
    return branch


@router.put("/{branch_id}", response_model=BranchResponse)
async def update_branch(
    branch_id: int,
    branch_in: BranchUpdate,
    db: AsyncSession = Depends(get_db),
    admin = Depends(get_current_active_admin)
):
    result = await db.execute(select(Branch).where(Branch.id == branch_id))
    branch = result.scalar_one_or_none()
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")

    data = branch_in.model_dump(exclude_unset=True)
    if data.get("operating_hours") and not data.get("opening_hours"):
        data["opening_hours"] = data.pop("operating_hours")
    valid_cols = {"name", "city", "address", "phone", "email", "latitude", "longitude", "opening_hours", "image_url", "is_active"}
    for field, val in data.items():
        if field in valid_cols:
            setattr(branch, field, val)

    await db.commit()
    await db.refresh(branch)
    return branch


@router.delete("/{branch_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_branch(
    branch_id: int,
    db: AsyncSession = Depends(get_db),
    admin = Depends(get_current_active_admin)
):
    result = await db.execute(select(Branch).where(Branch.id == branch_id))
    branch = result.scalar_one_or_none()
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")

    await db.delete(branch)
    await db.commit()
