from contextlib import asynccontextmanager
from typing import Generator, Any

from fastapi import FastAPI

from app import get_app
from settings import DatabaseSettings, AppSettings

db_settings = DatabaseSettings()
app_settings = AppSettings()


@asynccontextmanager
async def lifespan(_: FastAPI) -> Generator[Any, Any, None]:
    yield

app = get_app(app_settings, lifespan)
