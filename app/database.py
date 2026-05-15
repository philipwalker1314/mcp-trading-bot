from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
)
from sqlalchemy.ext.asyncio import (
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings
from app.logger import get_logger

logger = get_logger("database")


class Base(DeclarativeBase):
    pass


engine = create_async_engine(
    settings.postgres_url,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,
)


AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[
    AsyncSession,
    None,
]:

    async with AsyncSessionLocal() as session:

        try:
            yield session

        except Exception as error:

            logger.error(
                "database_session_error",
                error=str(error),
            )

            await session.rollback()

            raise

        finally:
            await session.close()


async def init_db():

    logger.info(
        "initializing_database",
    )

    async with engine.begin() as conn:

        await conn.run_sync(
            Base.metadata.create_all
        )

    logger.info(
        "database_initialized",
    )


async def close_db():

    logger.info(
        "closing_database",
    )

    await engine.dispose()

    logger.info(
        "database_closed",
    )
