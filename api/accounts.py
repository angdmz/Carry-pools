import http
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Body, Query
from fastapi.params import Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from enums import SortOrder
from logic.accounts import Account
from logic.accounts.business import RetrievedAccount, Address
from logic.participants import RetrievedParticipant, Participant, ParticipantListing, UpdateParticipant, ListLimit
from session.connection import get_async_session
from common import ObjRef

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
        ), session: AsyncSession = Depends(get_async_session)):
    async with session.begin() as tx:
        res = await ParticipantListing.from_persistance(persistance=tx, limit=limit, sort=sort,
                                                        timestamp_gt=timestamp_gt, timestamp_lt=timestamp_lt)
    return res


@router.get("/accounts/{address}", status_code=http.HTTPStatus.OK)
async def retrieve_account(address: Address = Path(..., description="Address to retrieve"),
                               session: AsyncSession = Depends(get_async_session)):
    async with session.begin() as tx:
        return await RetrievedAccount.from_persistance(address, persistance=tx)


@router.post("/accounts", status_code=http.HTTPStatus.CREATED)
async def create_account(account: Account = Body(..., description="Account data"),
                             session: AsyncSession = Depends(get_async_session)):
    async with session.begin() as tx:
        await account.persist_to(tx)
