from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.currency import Currency


class CurrencyService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_currencies(self):
        result = await self.session.execute(select(Currency))
        return result.scalars().all()