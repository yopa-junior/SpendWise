# app/main.py

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles  # 🔥 AJOUT
import os
from app.api.v1.router import api_router

from contextlib import asynccontextmanager
from app.tasks.scheduler import start_scheduler, scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Créer les dossiers pour les uploads
    os.makedirs("uploads/profiles", exist_ok=True)
    
    start_scheduler()
    yield
    scheduler.shutdown()


app = FastAPI(title="SpendWise API", lifespan=lifespan)


app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Routes
app.include_router(api_router, prefix="/api/v1")

# Health check (éviter le doublon avec la route "/")
@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "SpendWise API"}

@app.get("/")
async def root():
    return {"message": "SpendWise API is running"}