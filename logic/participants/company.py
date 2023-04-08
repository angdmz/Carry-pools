from datetime import datetime
from uuid import uuid4, UUID

from sqlalchemy import select
from typing_extensions import Literal

from pydantic import BaseModel

from enums import ParticipantType
from models import Participant as ParticipantModel, Company as CompanyModel
from logic.participants.exceptions import ParticipantNotFound


class CompanyParticipant(BaseModel):
    full_name: str
    cuit: str
    type: Literal[ParticipantType.COMPANY] = ParticipantType.COMPANY

    async def persist_to(self, persistence):
        participant = ParticipantModel(id=uuid4(), is_verified=False)
        company = CompanyModel(full_name=self.full_name, cuit=self.cuit, participant_id=participant.id, id=uuid4())
        persistence.add(participant)
        persistence.add(company)
        return participant.id


class RetrievedCompanyParticipant(CompanyParticipant):
    created_at: datetime
    is_verified: bool
    id: UUID

    def is_named(self, full_name):
        return self.full_name == full_name

    def has_cuit(self, cuit):
        return self.cuit == cuit


class UpdateCompanyParticipant(BaseModel):
    full_name: str | None
    cuit: str | None
    type: Literal[ParticipantType.COMPANY] = ParticipantType.COMPANY

    async def update_to_persistance(self, participant_id: UUID, persistance):
        values = self.dict(exclude_none=True)
        query = select(CompanyModel).select_from(CompanyModel).filter(CompanyModel.participant_id == participant_id)
        res = await persistance.execute(query)

        try:
            company = res.all()[0][0]
            for field, value in values.items():
                setattr(company, field, value)
        except IndexError:
            raise ParticipantNotFound(participant_id)
