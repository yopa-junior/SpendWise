# app/api/v1/router.py

from fastapi import APIRouter
from app.api.v1 import (
    auth,
    wallets,
    categories,
    users,
    expenses,
    budgets,
    statistics,
    notifications,
    ai,
    reports,
    reminders,
    currencies,
    exchange_rates,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(wallets.router)
api_router.include_router(categories.router)
api_router.include_router(users.router)
api_router.include_router(expenses.router)
api_router.include_router(budgets.router)
api_router.include_router(statistics.router)
api_router.include_router(notifications.router)
api_router.include_router(ai.router)
api_router.include_router(reports.router)
api_router.include_router(reminders.router)
api_router.include_router(currencies.router)
api_router.include_router(exchange_rates.router)
