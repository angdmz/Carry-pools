from datetime import datetime
from uuid import uuid4, UUID

from sqlalchemy import select
from typing_extensions import Literal

from pydantic import BaseModel

from enums import ParticipantType
from logic.participants.common import RetrievedParticipantBase
from models import Participant as ParticipantModel, GovernmentOrganism as GovernmentOrganismModel
from logic.participants.exceptions import ParticipantNotFound


class GovernmentOrganismParticipant(BaseModel):
    full_name: str
    sector: str
    type: Literal[ParticipantType.GOVERNMENT_ORGANISM] = ParticipantType.GOVERNMENT_ORGANISM

    async def persist_to(self, persistence):
        participant = ParticipantModel(id=uuid4(), is_verified=False, type=self.type)
        government_organism = GovernmentOrganismModel(full_name=self.full_name, sector=self.sector, id=uuid4(),
                                                      participant_id=participant.id)
        persistence.add(participant)
        persistence.add(government_organism)
        return participant.id


class RetrievedGovernmentOrganismParticipant(GovernmentOrganismParticipant, RetrievedParticipantBase):

    def is_named(self, name):
        return self.full_name == name

    def is_sector(self, sector):
        return self.sector == sector

    @staticmethod
    def add_columns_to_query(query):
        query = query.add_columns(GovernmentOrganismModel)
        return query

    @staticmethod
    def add_joins_to_query(query):
        query = query.join(GovernmentOrganismModel, isouter=True)
        return query

    @staticmethod
    def from_row(row):
        participant, organism = row
        parseable = dict(created_at=participant.created_at, is_verified=participant.is_verified, id=participant.id,
                         full_name=organism.full_name, sector=organism.sector)
        return RetrievedGovernmentOrganismParticipant.parse_obj(parseable)

class UpdateGovernmentOrganismParticipant(BaseModel):
    full_name: str | None
    sector: str | None
    type: Literal[ParticipantType.GOVERNMENT_ORGANISM] = ParticipantType.GOVERNMENT_ORGANISM

    async def update_to_persistance(self, participant_id: UUID, persistance):
        values = self.dict(exclude_none=True)
        query = select(GovernmentOrganismModel).select_from(GovernmentOrganismModel).filter(GovernmentOrganismModel.participant_id == participant_id)
        res = await persistance.execute(query)

        try:
            company = res.all()[0][0]
            for field, value in values.items():
                setattr(company, field, value)
        except IndexError:
            raise ParticipantNotFound(participant_id)
