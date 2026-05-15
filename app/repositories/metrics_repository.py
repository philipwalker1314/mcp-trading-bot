from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.models.metrics import Metric


class MetricsRepository:

    def __init__(
        self,
        db: AsyncSession,
    ):

        self.db = db

    async def create_metric(
        self,
        metric: Metric,
    ):

        self.db.add(metric)

        await self.db.commit()

        await self.db.refresh(metric)

        return metric

    async def list_metrics(self):

        query = select(Metric)

        result = await self.db.execute(
            query
        )

        return result.scalars().all()
