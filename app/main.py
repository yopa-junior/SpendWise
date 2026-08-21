from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os
from app.api.v1.router import api_router

from contextlib import asynccontextmanager
from app.tasks.scheduler import start_scheduler, scheduler


# Racine du projet SpendWise
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Dossier des uploads
UPLOADS_DIR = os.path.join(PROJECT_ROOT, "uploads")
PROFILES_DIR = os.path.join(UPLOADS_DIR, "profiles")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Créer les dossiers pour les uploads
    os.makedirs(PROFILES_DIR, exist_ok=True)

    start_scheduler()
    yield
    scheduler.shutdown()


app = FastAPI(
    title="SpendWise API",
    lifespan=lifespan
)


# Servir les fichiers uploadés
app.mount(
    "/uploads",
    StaticFiles(directory=UPLOADS_DIR),
    name="uploads"
)


# Routes
app.include_router(api_router, prefix="/api/v1")


# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "SpendWise API"
    }


@app.get("/")
async def root():
    return {
        "message": "SpendWise API is running"
    }