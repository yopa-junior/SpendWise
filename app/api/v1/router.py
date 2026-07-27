# app/api/v1/router.py

from fastapi import APIRouter
from app.api.v1 import auth, wallets
from app.api.v1 import auth, wallets, categories
from app.api.v1 import auth, wallets, categories, users
from app.api.v1 import auth, wallets, categories, users, expenses


api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(wallets.router)
api_router.include_router(categories.router)
api_router.include_router(users.router)
api_router.include_router(expenses.router)