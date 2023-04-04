from datetime import datetime
from uuid import uuid4, UUID

from pydantic import BaseModel
from sqlalchemy import select

from models.participants import Participant as ParticipantModel


class Participant(BaseModel):
    name: str

    async def persist_to(self, persistence):
        model = ParticipantModel(name=self.name, id=uuid4())
        persistence.add(model)
        return model.id


class RetrievedParticipant(Participant):
    created_at: datetime

    def is_named(self, name):
        return self.name == name

    @staticmethod
    async def from_persistance(participant_id: UUID, persistance):
        query = select(ParticipantModel).filter(ParticipantModel.id == participant_id)
        result = await persistance.execute(query)
        participant_model = result.all()[0][0]
        return RetrievedParticipant(name=participant_model.name, created_at=participant_model.created_at)
