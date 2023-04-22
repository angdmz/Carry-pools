import asyncpg
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from session.connection import get_async_session, generate_db_url
from settings import DatabaseSettings


def get_db_settings():
    return DatabaseSettings()

def get_db_url(db_settings: DatabaseSettings = Depends(get_db_settings)):
    return generate_db_url(db_settings)


async def get_session(db_url: str = Depends(get_db_url)) -> AsyncSession:
    async_session = get_async_session(db_url)
    async with async_session() as session:
        yield session



async def get_postgres_session(db_settings: DatabaseSettings = Depends(get_db_settings)):
    con = await asyncpg.connect(user=db_settings.db_username, password=db_settings.db_password, database=db_settings.db_name, host=db_settings.db_hostname, port=db_settings.db_port)
    yield con
    await con.close()