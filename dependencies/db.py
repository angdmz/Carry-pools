from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from session.connection import get_async_session
from settings import DatabaseSettings


def get_db_settings():
    return DatabaseSettings()


async def get_session(db_settings: DatabaseSettings = Depends(get_db_settings)) -> AsyncSession:
    async_session = get_async_session(db_settings)
    async with async_session() as session:
        yield session
