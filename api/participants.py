import http
from uuid import UUID

from fastapi import APIRouter, Body
from fastapi.params import Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from participants.business import Participant, RetrievedParticipant
from session.connection import get_async_session
from tests.schemas import ObjRef

router = APIRouter()


@router.get("/participants/{participant_id}", status_code=http.HTTPStatus.OK)
async def retrieve_participant(participant_id: UUID = Path(..., description="Participant ID to retrieve"), session: AsyncSession = Depends(get_async_session)):
    async with session.begin() as tx:
        return await RetrievedParticipant.from_persistance(participant_id, persistance=tx)


@router.post("/participants", status_code=http.HTTPStatus.CREATED)
async def create_participant(participant: Participant = Body(..., description="Participant data"), session: AsyncSession = Depends(get_async_session)):
    async with session.begin() as tx:
        participant_id = await participant.persist_to(tx)
    return ObjRef(id=participant_id)
