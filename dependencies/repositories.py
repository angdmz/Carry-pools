from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies.db import get_session
from repositories.vesting_schedules import Repository


def get_vesting_schedule_repository(session: AsyncSession = Depends(get_session)):
    return Repository(session)
