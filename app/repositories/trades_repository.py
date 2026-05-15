from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.models.trades import Trade


class TradesRepository:

    def __init__(
        self,
        db: AsyncSession,
    ):

        self.db = db

    async def create_trade(
        self,
        trade: Trade,
    ):

        self.db.add(trade)

        await self.db.commit()

        await self.db.refresh(trade)

        return trade

    async def get_trade(
        self,
        trade_id: int,
    ):

        query = select(Trade).where(
            Trade.id == trade_id
        )

        result = await self.db.execute(
            query
        )

        return result.scalar_one_or_none()

    async def list_trades(self):

        query = select(Trade)

        result = await self.db.execute(
            query
        )

        return result.scalars().all()
