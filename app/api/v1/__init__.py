from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.content import router as content_router
from app.api.v1.menu import router as menu_router
from app.api.v1.reservations import router as reservations_router
from app.api.v1.payments import router as payments_router
from app.api.v1.reviews import router as reviews_router
from app.api.v1.navigation import router as navigation_router
from app.api.v1.branches import router as branches_router
from app.api.v1.banner_slides import router as banner_slides_router
from app.api.v1.stories import router as stories_router
from app.api.v1.pages import router as pages_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(content_router)
api_router.include_router(menu_router)
api_router.include_router(reservations_router)
api_router.include_router(payments_router)
api_router.include_router(reviews_router)
api_router.include_router(navigation_router)
api_router.include_router(branches_router)
api_router.include_router(banner_slides_router)
api_router.include_router(stories_router)
api_router.include_router(pages_router)
