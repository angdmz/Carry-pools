import http
from datetime import datetime
from typing import Set
from uuid import UUID

from fastapi import APIRouter, Query, Body
from fastapi.params import Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from common import ObjRef
from dependencies.db import get_session
from dependencies.repositories import get_vesting_schedule_repository
from enums import SortOrder, RechargeStatus
from logic.accounts.business import Address
from logic.carry_pools import VestingSchedule
from logic.participants import ListLimit
from logic.recharges.recharge import RetrievedRecharge, RetrievedWaitingRecharge, RechargeListing
from repositories.vesting_schedules import Repository

router = APIRouter()


@router.get("/vesting-schedules", status_code=http.HTTPStatus.OK)
async def list_vesting_schedules(
        limit: ListLimit = Query(10, description=""),
        sort: SortOrder = Query(SortOrder.DESC, description=""),
        status: Set[RechargeStatus] | None = Query(None, description="Only include recharges with these statuses"),
        recharge_ids: Set[UUID] | None = Query(None, description="Only include recharges with these recharge ids"),
        participant_ids: Set[UUID] | None = Query(None, description="Only include recharges from these participants"),
        addresses: Set[Address] | None = Query(None, description="Only include recharges from these addresses"),
        timestamp_gt: datetime | None = Query(
            None, description="Only include recharges created with timestamps greater than this value."
        ),
        timestamp_lt: datetime | None = Query(
            None, description="Only include recharges created with timestamps less than this value."
        ),
        session: AsyncSession = Depends(get_session)):
    async with session.begin():
        res = await RechargeListing.from_persistance(persistance=session, limit=limit, sort=sort, status=status,
                                                     addresses=addresses, recharge_ids=recharge_ids,
                                                     participant_ids=participant_ids, timestamp_gt=timestamp_gt,
                                                     timestamp_lt=timestamp_lt)
    return res


@router.get("/vesting-schedules/{vesting_schedule_id}", status_code=http.HTTPStatus.OK)
async def retrieve_vesting_schedule(vesting_schedule_id: UUID = Path(..., description="Recharge to retrieve"),vesting_schedule_repository: Repository=Depends(get_vesting_schedule_repository),
                            session: AsyncSession = Depends(get_session)):
    async with session.begin():
        return await RetrievedRecharge.from_persistance(recharge_id, persistance=session)


@router.post("/vesting-schedules", status_code=http.HTTPStatus.ACCEPTED)
async def create_vesting_schedule(vesting_schedule: VestingSchedule = Body(..., description="Vesting schedule data"),vesting_schedule_repository: Repository=Depends(get_vesting_schedule_repository),
                             session: AsyncSession = Depends(get_session)):
    async with session.begin():
        vesting_schedule_id = await vesting_schedule.persist_to(vesting_schedule_repository)
    return ObjRef(id=vesting_schedule_id)



@router.patch("/vesting-schedules/{vesting_schedule_id}/reject", status_code=http.HTTPStatus.ACCEPTED)
async def update_vesting_schedule(vesting_schedule_id: UUID = Path(..., description="Recharge ID"),
                             session: AsyncSession = Depends(get_session)):
    async with session.begin():
        waiting_recharge = await RetrievedWaitingRecharge.from_persistance(recharge_id, session)
        rejected_recharge = await waiting_recharge.reject()
        await rejected_recharge.persist_to(session)
