import http
from datetime import datetime
from uuid import UUID

from asyncpg import Connection
from fastapi import APIRouter, Body, Query
from fastapi.params import Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from common import ObjRef
from dependencies.accounts import get_balance_limit_per_account
from dependencies.db import get_session, get_postgres_session
from enums import SortOrder
from logic.accounts import Account
from logic.accounts.business import RetrievedAccount, Address, UnverifiedController, AddressCollection
from logic.participants import ParticipantListing, ListLimit
from logic.recharges.recharge import Recharge

router = APIRouter()


@router.get("/accounts", status_code=http.HTTPStatus.OK)
async def list_accounts(
        limit: ListLimit = Query(10, description=""),
        sort: SortOrder = Query(SortOrder.DESC, description=""),
        timestamp_gt: datetime | None = Query(
            None, description="Only include accounts created with timestamps greater than this value."
        ),
        timestamp_lt: datetime | None = Query(
            None, description="Only include accounts created with timestamps less than this value."
        ), session: AsyncSession = Depends(get_session)):
    async with session.begin():
        res = await ParticipantListing.from_persistance(persistance=session, limit=limit, sort=sort,
                                                        timestamp_gt=timestamp_gt, timestamp_lt=timestamp_lt)
    return res


@router.get("/accounts/{address}", status_code=http.HTTPStatus.OK)
async def retrieve_account(address: Address = Path(..., description="Address to retrieve"),
                               session: AsyncSession = Depends(get_session)):
    async with session.begin():
        return await RetrievedAccount.from_persistance(address, persistance=session)


@router.post("/accounts", status_code=http.HTTPStatus.CREATED)
async def create_account(account: Account = Body(..., description="Account data"),
                         balance_limit_per_account = Depends(get_balance_limit_per_account),
                             session: AsyncSession = Depends(get_session)):
    async with session.begin():
        await account.persist_to(session, balance_limit_per_account)


@router.post("/controllers/{participant_id}/verifications/{address}", status_code=http.HTTPStatus.ACCEPTED)
async def verify_address_control(participant_id: UUID = Path(..., description="Participant ID"),
                           address: Address = Path(..., description="Address to request"),
                             session: AsyncSession = Depends(get_session)):
    async with session.begin():
        controller = await UnverifiedController.from_persistance(address, participant_id, session)
        verified_controller = controller.verify()
        await verified_controller.persist_to(session)


@router.post("/accounts/{address}/recharges", status_code=http.HTTPStatus.ACCEPTED)
async def request_recharge(address: Address = Path(..., description="Address to request"),
                           session: AsyncSession = Depends(get_session)):
    async with session.begin():
        recharge = Recharge.waiting_for(address)
        recharge_id = await recharge.persist_to(session)
        return ObjRef(id=recharge_id)


@router.patch("/accounts/balances", status_code=http.HTTPStatus.OK)
async def update_balances(new_balances: AddressCollection = Body(..., description="Balances to update"),
                          session: Connection = Depends(get_postgres_session)):
    async with session.transaction():
        await new_balances.persist_to(session)
