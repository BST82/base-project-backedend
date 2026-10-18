from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_active_admin
from app.models.menu import Category, MenuItem
from app.schemas.menu import (
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
    MenuItemCreate,
    MenuItemUpdate,
    MenuItemResponse,
)

router = APIRouter(prefix="/menu", tags=["Menu & Recipes"])


# ==============================================================================
# Categories
# ==============================================================================

@router.get("/categories", response_model=List[CategoryResponse])
async def list_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category).order_by(Category.display_order, Category.name))
    return result.scalars().all()


@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    cat_in: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_active_admin)
):
    existing = await db.execute(select(Category).where(Category.slug == cat_in.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Category with this slug already exists")
    
    category = Category(**cat_in.model_dump())
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


@router.put("/categories/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    cat_in: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_active_admin)
):
    result = await db.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    for field, val in cat_in.model_dump(exclude_unset=True).items():
        setattr(category, field, val)
        
    await db.commit()
    await db.refresh(category)
    return category


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_active_admin)
):
    result = await db.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    await db.delete(category)
    await db.commit()


# ==============================================================================
# Menu Items & Recipes
# ==============================================================================

@router.get("/items", response_model=List[MenuItemResponse])
async def list_menu_items(
    category_id: Optional[int] = None,
    is_top_recipe: Optional[bool] = None,
    is_chef_special: Optional[bool] = None,
    in_stock_only: bool = False,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(MenuItem).options(selectinload(MenuItem.category))
    
    if category_id:
        query = query.where(MenuItem.category_id == category_id)
    if is_top_recipe is not None:
        query = query.where(MenuItem.is_top_recipe == is_top_recipe)
    if is_chef_special is not None:
        query = query.where(MenuItem.is_chef_special == is_chef_special)
    if in_stock_only:
        query = query.where(MenuItem.in_stock == True)
    if search:
        search_fmt = f"%{search.strip()}%"
        query = query.where(
            (MenuItem.name.ilike(search_fmt)) |
            (MenuItem.description.ilike(search_fmt)) |
            (MenuItem.tags.ilike(search_fmt))
        )
    
    result = await db.execute(query.order_by(MenuItem.name))
    return result.scalars().all()


@router.get("/items/{item_id}", response_model=MenuItemResponse)
async def get_menu_item(item_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MenuItem).options(selectinload(MenuItem.category)).where(MenuItem.id == item_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    return item


@router.post("/items", response_model=MenuItemResponse, status_code=status.HTTP_201_CREATED)
async def create_menu_item(
    item_in: MenuItemCreate,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_active_admin)
):
    cat_check = await db.execute(select(Category).where(Category.id == item_in.category_id))
    if not cat_check.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Associated category does not exist")

    item = MenuItem(**item_in.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    
    # Reload with category relation
    res = await db.execute(
        select(MenuItem).options(selectinload(MenuItem.category)).where(MenuItem.id == item.id)
    )
    return res.scalar_one()


@router.put("/items/{item_id}", response_model=MenuItemResponse)
async def update_menu_item(
    item_id: int,
    item_in: MenuItemUpdate,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_active_admin)
):
    result = await db.execute(select(MenuItem).where(MenuItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")

    for field, val in item_in.model_dump(exclude_unset=True).items():
        setattr(item, field, val)

    await db.commit()
    
    res = await db.execute(
        select(MenuItem).options(selectinload(MenuItem.category)).where(MenuItem.id == item.id)
    )
    return res.scalar_one()


@router.patch("/items/{item_id}/toggle-stock", response_model=MenuItemResponse)
async def toggle_menu_item_stock(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_active_admin)
):
    result = await db.execute(select(MenuItem).where(MenuItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")

    item.in_stock = not item.in_stock
    await db.commit()
    
    res = await db.execute(
        select(MenuItem).options(selectinload(MenuItem.category)).where(MenuItem.id == item.id)
    )
    return res.scalar_one()


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_menu_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_active_admin)
):
    result = await db.execute(select(MenuItem).where(MenuItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")

    await db.delete(item)
    await db.commit()
