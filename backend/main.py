import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Ensure both project root and backend directory are in sys.path
_backend_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_backend_dir)
for _p in [_parent_dir, _backend_dir]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import PROJECT_NAME, VERSION, STORAGE_DRIVER
from backend.database import init_db
from backend.cloud.database_service import seed_initial_demo_data
from backend.routes.auth_routes import router as auth_router
from backend.routes.assignment_routes import router as assignment_router
from backend.routes.submission_routes import router as submission_router
from backend.routes.grading_routes import router as grading_router
from backend.routes.dashboard_routes import router as dashboard_router
from backend.routes.similarity_routes import router as similarity_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQL Database Schema
    init_db()
    # Seed initial demo profiles and sample courses
    seed_initial_demo_data()
    yield

app = FastAPI(
    title=PROJECT_NAME,
    version=VERSION,
    description="Industry-Oriented Cloud-Based Student Assignment Submission & Feedback Portal REST API",
    lifespan=lifespan
)

# Cross-Origin Resource Sharing (CORS) for Cloud / Microservice decoupling (Vercel, Render, Local)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(auth_router)
app.include_router(assignment_router)
app.include_router(submission_router)
app.include_router(grading_router)
app.include_router(dashboard_router)
app.include_router(similarity_router)

from backend.database import init_db, IS_POSTGRES
from backend.cloud.supabase_service import supabase_service

# Health Check & Cloud Monitoring Endpoint
@app.get("/api/health", tags=["Cloud Health"])
def health_check():
    """Liveness and readiness probe for Cloud Orchestrator / Load Balancer."""
    return {
        "status": "healthy",
        "service": PROJECT_NAME,
        "version": VERSION,
        "environment": "cloud-ready",
        "database": "supabase-postgresql" if IS_POSTGRES else "sqlite-wal",
        "storage_driver": STORAGE_DRIVER,
        "supabase": supabase_service.health_check()
    }

# Mount Frontend static files
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
