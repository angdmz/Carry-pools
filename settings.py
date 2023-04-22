from typing import Sequence

from pydantic import BaseSettings, SecretStr, AnyHttpUrl, PositiveInt


class DatabaseSettings(BaseSettings):
    db_url_prefix: str = "postgresql+asyncpg"
    db_hostname: str = "localhost"
    db_port: int = 5432
    db_username: str
    db_password: str
    db_name: str
    db_schema: str = "banking_db"
    db_secret: SecretStr
    db_secret_key: SecretStr


class AppSettings(BaseSettings):
    sentry_dsn: str | None = None
    path_prefix: str = ""
    api_cors_origins: Sequence[AnyHttpUrl] = ()


class AccountsSettings(BaseSettings):
    balance_limit: PositiveInt = 100000000
