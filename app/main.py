import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.db.init_db import init_database, seed_initial_data
from app.api.v1 import api_router

UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "uploads"))
os.makedirs(UPLOAD_DIR, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables exist and seed default admin/CMS data
    try:
        print("[INFO] Connecting to PostgreSQL database and initializing tables...")
        await init_database()
        print("[INFO] Tables verified/created successfully. Seeding initial data...")
        async with AsyncSessionLocal() as session:
            await seed_initial_data(session)
        print("[INFO] Database successfully initialized and seeded with Navigation, Branches, Slider & Stories!")
    except Exception as e:
        print(f"[ERROR] Database initialization error: {e}")
    yield
    # Shutdown logic if any


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded assets (photos, logo)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Include API v1 routes
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT
    }


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")
