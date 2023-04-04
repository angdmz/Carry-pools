from typing import Type

from fastapi.params import Depends
from sqlalchemy import URL
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from settings import DatabaseSettings


def get_db_settings():
    return DatabaseSettings()


def generate_db_url(settings: DatabaseSettings = Depends(get_db_settings)):
    return URL.create(
        drivername=settings.db_url_prefix,
        username=settings.db_username,
        password=settings.db_password,
        host=settings.db_hostname,
        port=settings.db_port,
        database=settings.db_name,
    )


def get_async_session(database_url: str = Depends(generate_db_url)) -> Type[AsyncSession]:
    engine = create_async_engine(database_url, echo=True, future=True)

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )

    return async_session


Base = declarative_base()
