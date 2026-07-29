# app/tasks/scheduler.py

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.database.database import AsyncSessionLocal
from app.services.report_service import ReportService

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def run_monthly_reports_job():
    """Job exécuté automatiquement le 1er de chaque mois à 6h du matin."""
    logger.info("Démarrage de la génération des résumés mensuels")
    async with AsyncSessionLocal() as session:
        service = ReportService(session)
        count = await service.generate_monthly_reports_for_all_users()
    logger.info(f"Résumés mensuels générés pour {count} utilisateur(s)")


def start_scheduler():
    scheduler.add_job(
        run_monthly_reports_job,
        trigger=CronTrigger(day=1, hour=6, minute=0),
        id="monthly_reports",
        replace_existing=True,
    )
    scheduler.start()