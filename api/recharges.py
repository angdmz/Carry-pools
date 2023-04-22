import http
from datetime import datetime
from typing import Set
from uuid import UUID

from fastapi import APIRouter, Query
from fastapi.params import Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from common import ObjRef
from dependencies.db import get_session
from enums import SortOrder, RechargeStatus
from logic.accounts.business import Address
from logic.participants import ListLimit
from logic.recharges.recharge import Recharge, RetrievedRecharge, RetrievedWaitingRecharge, RechargeListing

router = APIRouter()


@router.get("/recharges", status_code=http.HTTPStatus.OK)
async def list_recharges(
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


@router.get("/recharges/{recharge_id}", status_code=http.HTTPStatus.OK)
async def retrieve_recharge(recharge_id: UUID = Path(..., description="Recharge to retrieve"),
                            session: AsyncSession = Depends(get_session)):
    async with session.begin():
        return await RetrievedRecharge.from_persistance(recharge_id, persistance=session)


@router.post("/recharges/{recharge_id}/satisfy", status_code=http.HTTPStatus.ACCEPTED)
async def satisfy_recharge(recharge_id: UUID = Path(..., description="Recharge ID"),
                             session: AsyncSession = Depends(get_session)):
    async with session.begin():
        waiting_recharge = await RetrievedWaitingRecharge.from_persistance(recharge_id, session)
        satisfied_recharge = await waiting_recharge.satisfy()
        await satisfied_recharge.persist_to(session)


@router.post("/recharges/{recharge_id}/reject", status_code=http.HTTPStatus.ACCEPTED)
async def satisfy_recharge(recharge_id: UUID = Path(..., description="Recharge ID"),
                             session: AsyncSession = Depends(get_session)):
    async with session.begin():
        waiting_recharge = await RetrievedWaitingRecharge.from_persistance(recharge_id, session)
        rejected_recharge = await waiting_recharge.reject()
        await rejected_recharge.persist_to(session)


@router.post("/accounts/{address}/recharges", status_code=http.HTTPStatus.ACCEPTED)
async def request_recharge(address: Address = Path(..., description="Address to request"),
                           session: AsyncSession = Depends(get_session)):
    async with session.begin():
        recharge = Recharge.waiting_for(address)
        recharge_id = await recharge.persist_to(session)
        return ObjRef(id=recharge_id)
