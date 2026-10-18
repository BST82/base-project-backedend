import os
import uuid
import aiofiles
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_active_admin
from app.models.dynamic_page import DynamicPage
from app.models.navigation import NavItem
from app.schemas.dynamic_page import (
    DynamicPageCreate,
    DynamicPageUpdate,
    DynamicPageResponse,
)

router = APIRouter(prefix="/pages", tags=["Dynamic Pages CMS"])

UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads"))
os.makedirs(UPLOAD_DIR, exist_ok=True)


def default_content_blocks(title: str, subtitle: str) -> list:
    return [
        {
            "id": f"block-{uuid.uuid4().hex[:8]}",
            "block_type": "rich_text",
            "badge": "PHILOSOPHY & VISION",
            "heading": f"Welcome to {title}",
            "subheading": subtitle or "Curated farm harvests, fire-forged culinary craft, and unhurried hospitality.",
            "body": "<p>At Aura Bistro, every plate and gathering is crafted from seed to flame with organic integrity. We partner directly with family regeneratively-farmed growers, cold-pressing our oils and milling heritage grains daily.</p><p>Explore our seasonal selections, inquire about custom tastings, and let our culinary team tailor an unforgettable experience for your table.</p>",
            "image_url": ""
        },
        {
            "id": f"block-{uuid.uuid4().hex[:8]}",
            "block_type": "split_content",
            "badge": "ARTISAN CRAFT",
            "heading": "Fire, Earth & Seasonal Integrity",
            "subheading": "Five to seven course tasting experiences designed with nature's rhythm.",
            "body": "<p>Our hearth blazes with fragrant aged Californian applewood at 750°F, marrying primal binchotan heat with delicate botanical reductions. Every element is balanced to honor human biology and genuine culinary mastery.</p>",
            "image_url": "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=1200&q=80",
            "button_text": "Reserve Hearth Table",
            "button_link": "/reserve"
        },
        {
            "id": f"block-{uuid.uuid4().hex[:8]}",
            "block_type": "feature_grid",
            "badge": "EXPERIENCE PILLARS",
            "heading": "Signature Highlights",
            "subheading": "What defines our hospitality and craft",
            "items": [
                {
                    "icon": "🌾",
                    "title": "100% Regenerative Sourcing",
                    "description": "Produce harvested under 24 hours prior to service directly from partner farms."
                },
                {
                    "icon": "🔥",
                    "title": "Woodfired Mastery",
                    "description": "Charcoal and hearth flame cooking preserving vital nutrients and unmatched umami."
                },
                {
                    "icon": "🍷",
                    "title": "Natural Wine Guild",
                    "description": "Low-intervention organic vintages and biodynamic cellar pairings by certified sommeliers."
                }
            ]
        },
        {
            "id": f"block-{uuid.uuid4().hex[:8]}",
            "block_type": "cta_banner",
            "badge": "JOIN OUR TABLE",
            "heading": "Ready to Experience This in Person?",
            "subheading": "Book your table online or connect with our guest hospitality concierge.",
            "button_text": "Make a Reservation",
            "button_link": "/reserve"
        }
    ]


@router.get("", response_model=List[DynamicPageResponse])
async def list_dynamic_pages(db: AsyncSession = Depends(get_db)):
    """Admin endpoint: lists all dynamic pages."""
    result = await db.execute(select(DynamicPage).order_by(DynamicPage.id.desc()))
    return result.scalars().all()


@router.get("/{slug}", response_model=DynamicPageResponse)
async def get_page_by_slug(slug: str, db: AsyncSession = Depends(get_db)):
    """Public endpoint: fetches page data and layout by slug (or route)."""
    clean_slug = slug.strip().strip("/").lower()
    result = await db.execute(select(DynamicPage).where(DynamicPage.slug == clean_slug))
    page = result.scalar_one_or_none()
    if not page:
        # Fallback query by starting with /slug
        result = await db.execute(select(DynamicPage).where(DynamicPage.slug == f"/{clean_slug}"))
        page = result.scalar_one_or_none()

    if not page:
        raise HTTPException(status_code=404, detail=f"Dynamic page '{slug}' not found")
    return page


@router.post("", response_model=DynamicPageResponse, status_code=status.HTTP_201_CREATED)
async def create_dynamic_page(
    page_in: DynamicPageCreate,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_active_admin)
):
    clean_slug = page_in.slug.strip().strip("/").lower()
    # Check if slug exists
    existing = await db.execute(select(DynamicPage).where(DynamicPage.slug == clean_slug))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"Page with slug '{clean_slug}' already exists")

    hero_slides = page_in.hero_slides or [
        {
            "image_url": "https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=2000&q=85",
            "badge_text": "AURA CURATED GATHERINGS",
            "title": page_in.title.upper(),
            "subtitle": page_in.subtitle or "Artisanal culinary journeys crafted with farm-to-table excellence.",
            "caption": "EST. 2026 • SCRATCH KITCHEN",
            "button_primary_text": "Reserve an Experience",
            "button_primary_link": "/reserve"
        }
    ]

    content_blocks = page_in.content_blocks or default_content_blocks(page_in.title, page_in.subtitle or "")

    page = DynamicPage(
        nav_item_id=page_in.nav_item_id,
        slug=clean_slug,
        title=page_in.title,
        subtitle=page_in.subtitle,
        meta_description=page_in.meta_description,
        hero_slides=hero_slides,
        content_blocks=content_blocks,
        is_published=page_in.is_published,
    )
    db.add(page)
    await db.commit()
    await db.refresh(page)
    return page


@router.put("/{page_id}", response_model=DynamicPageResponse)
async def update_dynamic_page(
    page_id: int,
    page_in: DynamicPageUpdate,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_active_admin)
):
    result = await db.execute(select(DynamicPage).where(DynamicPage.id == page_id))
    page = result.scalar_one_or_none()
    if not page:
        raise HTTPException(status_code=404, detail="Dynamic page not found")

    update_data = page_in.model_dump(exclude_unset=True)
    if "slug" in update_data and update_data["slug"]:
        update_data["slug"] = update_data["slug"].strip().strip("/").lower()
        # Verify unique slug
        chk = await db.execute(select(DynamicPage).where(DynamicPage.slug == update_data["slug"], DynamicPage.id != page_id))
        if chk.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Slug already in use by another page")

    for field, val in update_data.items():
        setattr(page, field, val)

    await db.commit()
    await db.refresh(page)
    return page


@router.delete("/{page_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dynamic_page(
    page_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_active_admin)
):
    result = await db.execute(select(DynamicPage).where(DynamicPage.id == page_id))
    page = result.scalar_one_or_none()
    if not page:
        raise HTTPException(status_code=404, detail="Dynamic page not found")

    await db.delete(page)
    await db.commit()


@router.post("/upload-asset")
async def upload_page_asset(
    file: UploadFile = File(...),
    admin=Depends(get_current_active_admin)
):
    """Upload hero slide or content block image."""
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png", ".webp", ".svg"]:
        raise HTTPException(status_code=400, detail="Unsupported image format")

    filename = f"page_{uuid.uuid4().hex}{ext}"
    content_bytes = await file.read()

    backend_base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    dirs_to_save = [
        UPLOAD_DIR,
        os.path.abspath(os.path.join(backend_base, "backend", "uploads")),
        os.path.abspath(os.path.join(backend_base, "backend", "app", "uploads")),
        os.path.abspath(os.path.join(backend_base, "frontend", "public", "uploads")),
    ]
    for d in set(dirs_to_save):
        try:
            os.makedirs(d, exist_ok=True)
            async with aiofiles.open(os.path.join(d, filename), "wb") as out_file:
                await out_file.write(content_bytes)
        except Exception:
            pass

    return {"url": f"/uploads/{filename}", "filename": filename}
