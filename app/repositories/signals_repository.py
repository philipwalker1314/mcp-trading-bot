from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.models.signals import Signal


class SignalsRepository:

    def __init__(
        self,
        db: AsyncSession,
    ):

        self.db = db

    async def create_signal(
        self,
        signal: Signal,
    ):

        self.db.add(signal)

        await self.db.commit()

        await self.db.refresh(signal)

        return signal

    async def list_signals(self):

        query = select(Signal)

        result = await self.db.execute(
            query
        )

        return result.scalars().all()
