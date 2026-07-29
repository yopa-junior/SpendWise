# app/main.py

from fastapi import FastAPI
from app.api.v1.router import api_router

from contextlib import asynccontextmanager
from app.tasks.scheduler import start_scheduler, scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    scheduler.shutdown()


app = FastAPI(title="SpendWise API", lifespan=lifespan)

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "SpendWise API is running"}