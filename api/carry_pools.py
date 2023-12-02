import http
from datetime import datetime
from typing import Set
from uuid import UUID

from fastapi import APIRouter, Query, Body
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from common import ObjRef
from dependencies.db import get_session
from dependencies.repositories import get_vesting_schedule_repository
from logic.carry_pools import VestingSchedule
from repositories.vesting_schedules import Repository

router = APIRouter()


@router.post("/vesting-schedules", status_code=http.HTTPStatus.ACCEPTED)
async def create_vesting_schedule(vesting_schedule: VestingSchedule = Body(..., description="Vesting schedule data"),
                                  vesting_schedule_repository: Repository=Depends(get_vesting_schedule_repository),
                                  session: AsyncSession = Depends(get_session)):
    async with session.begin():
        vesting_schedule_id = await vesting_schedule_repository.persist(vesting_schedule)
    return ObjRef(id=vesting_schedule_id)
