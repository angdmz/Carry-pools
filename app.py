import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from settings import AppSettings
from api import participants_router


def get_app(settings: AppSettings, lifespan):

    app = FastAPI(
        title="Registración BFA",
        lifespan=lifespan
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.api_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    sentry_sdk.init(
        dsn=settings.sentry_dsn, integrations=[StarletteIntegration(), FastApiIntegration()]
    )

    app.include_router(participants_router)
    return app