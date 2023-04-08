import http
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Body, Query
from fastapi.params import Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from enums import SortOrder
from logic.participants import RetrievedParticipant, Participant, ParticipantListing, UpdateParticipant, ListLimit
from session.connection import get_async_session
from common import ObjRef

router = APIRouter()


@router.get("/participants", status_code=http.HTTPStatus.OK)
async def list_participants(
        limit: ListLimit = Query(10, description=""),
        sort: SortOrder = Query(SortOrder.DESC, description=""),
        verified: bool | None = Query(
            None, description="Optional boolean to include only verified or unverified participants."
        ),
        timestamp_gt: datetime | None = Query(
            None, description="Only include participants created with timestamps greater than this value."
        ),
        timestamp_lt: datetime | None = Query(
            None, description="Only include participants created with timestamps less than this value."
        ), session: AsyncSession = Depends(get_async_session)):
    async with session.begin() as tx:
        res = await ParticipantListing.from_persistance(persistance=tx, limit=limit, sort=sort, verified=verified,
                                                        timestamp_gt=timestamp_gt, timestamp_lt=timestamp_lt)
    return res

@router.get("/participants/{participant_id}", status_code=http.HTTPStatus.OK)
async def retrieve_participant(participant_id: UUID = Path(..., description="Participant ID to retrieve"),
                               session: AsyncSession = Depends(get_async_session)):
    async with session.begin() as tx:
        return await RetrievedParticipant.from_persistance(participant_id, persistance=tx)


@router.patch("/participants/{participant_id}", status_code=http.HTTPStatus.NO_CONTENT)
async def update_participant(
        participant_id: UUID = Path(..., description="Participant ID to update"),
        participant: UpdateParticipant = Body(..., description="Participant data"),
                             session: AsyncSession = Depends(get_async_session)):
    async with session.begin() as tx:
        await participant.update_to_persistance(participant_id, tx)


@router.post("/participants", status_code=http.HTTPStatus.CREATED)
async def create_participant(participant: Participant = Body(..., description="Participant data"),
                             session: AsyncSession = Depends(get_async_session)):
    async with session.begin() as tx:
        participant_id = await participant.persist_to(tx)
    return ObjRef(id=participant_id)


