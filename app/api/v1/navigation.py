import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_active_admin
from app.models.navigation import NavItem
from app.models.dynamic_page import DynamicPage
from app.schemas.navigation import NavItemCreate, NavItemUpdate, NavItemResponse
from app.api.v1.pages import default_content_blocks

router = APIRouter(prefix="/navigation", tags=["Header & Navigation CMS"])


def map_nav_item_response(item: NavItem) -> NavItemResponse:
    has_page = item.dynamic_page is not None
    slug = item.dynamic_page.slug if has_page else None
    return NavItemResponse(
        id=item.id,
        label=item.label,
        route=item.route,
        display_order=item.display_order,
        is_active=item.is_active,
        is_external=item.is_external,
        created_at=item.created_at,
        has_dynamic_page=has_page,
        page_slug=slug,
    )


@router.get("", response_model=List[NavItemResponse])
async def list_active_nav_items(db: AsyncSession = Depends(get_db)):
    """Public endpoint: returns all active navigation menu items ordered by display_order."""
    result = await db.execute(
        select(NavItem)
        .options(selectinload(NavItem.dynamic_page))
        .where(NavItem.is_active == True)
        .order_by(NavItem.display_order, NavItem.id)
    )
    items = result.scalars().all()
    return [map_nav_item_response(i) for i in items]


@router.get("/admin/all", response_model=List[NavItemResponse])
async def list_all_nav_items(db: AsyncSession = Depends(get_db)):
    """Admin endpoint: returns all navigation items including inactive ones."""
    result = await db.execute(
        select(NavItem)
        .options(selectinload(NavItem.dynamic_page))
        .order_by(NavItem.display_order, NavItem.id)
    )
    items = result.scalars().all()
    return [map_nav_item_response(i) for i in items]


@router.post("", response_model=NavItemResponse, status_code=status.HTTP_201_CREATED)
async def create_nav_item(item_in: NavItemCreate, db: AsyncSession = Depends(get_db)):
    """
    Single transactional flow:
    Creates a navigation menu tab and automatically scaffolds a layout-inherited DynamicPage
    with hero banner slider and modular content blocks if requested.
    """
    clean_route = item_in.route.strip()
    if not clean_route.startswith("/") and not item_in.is_external:
        clean_route = f"/{clean_route}"

    clean_slug = clean_route.strip("/").lower()

    # Create NavItem entity
    nav_item = NavItem(
        label=item_in.label,
        route=clean_route,
        display_order=item_in.display_order,
        is_active=item_in.is_active,
        is_external=item_in.is_external,
    )
    db.add(nav_item)
    await db.flush()  # Flush to obtain nav_item.id within current transaction

    # Check if a dynamic page should be scaffolded
    hardcoded_routes = ["", "menu", "reserve", "locations", "stories", "reviews", "admin"]
    should_create_page = item_in.create_page or (not item_in.is_external and clean_slug not in hardcoded_routes)

    if should_create_page and clean_slug:
        # Check if page with this slug already exists
        page_check = await db.execute(select(DynamicPage).where(DynamicPage.slug == clean_slug))
        if not page_check.scalar_one_or_none():
            page_title = item_in.page_title or item_in.label
            page_subtitle = item_in.page_subtitle or f"Discover handcrafted seasonal experiences at {item_in.label}."
            hero_image = item_in.page_hero_image or "https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=2000&q=85"

            hero_slides = [
                {
                    "image_url": hero_image,
                    "badge_text": f"EST. 2026 • {item_in.label.upper()}",
                    "title": page_title.upper(),
                    "subtitle": page_subtitle,
                    "caption": "ARTISAN GASTRONOMY & HOSPITALITY",
                    "button_primary_text": "Reserve a Table",
                    "button_primary_link": "/reserve",
                    "button_secondary_text": "Explore Menus",
                    "button_secondary_link": "/menu"
                }
            ]

            content_blocks = default_content_blocks(page_title, page_subtitle)

            dynamic_page = DynamicPage(
                nav_item_id=nav_item.id,
                slug=clean_slug,
                title=page_title,
                subtitle=page_subtitle,
                meta_description=page_subtitle,
                hero_slides=hero_slides,
                content_blocks=content_blocks,
                is_published=True,
            )
            db.add(dynamic_page)

    # Commit both entities atomically in a single transactional flow
    await db.commit()

    # Reload with dynamic_page loaded
    reloaded = await db.execute(
        select(NavItem)
        .options(selectinload(NavItem.dynamic_page))
        .where(NavItem.id == nav_item.id)
    )
    final_item = reloaded.scalar_one()
    return map_nav_item_response(final_item)


@router.put("/{item_id}", response_model=NavItemResponse)
async def update_nav_item(item_id: int, item_in: NavItemUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(NavItem)
        .options(selectinload(NavItem.dynamic_page))
        .where(NavItem.id == item_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Navigation item not found")

    for field, val in item_in.model_dump(exclude_unset=True).items():
        setattr(item, field, val)

    await db.commit()
    await db.refresh(item)
    return map_nav_item_response(item)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_nav_item(item_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(NavItem).where(NavItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Navigation item not found")

    await db.delete(item)
    await db.commit()
