from datetime import datetime
from uuid import uuid4, UUID

from typing_extensions import Literal

from pydantic import BaseModel

from enums import IdentificationType, ParticipantType
from models import Participant as ParticipantModel, NaturalPerson as NaturalPersonModel, \
    Identification as IdentificationModel


class Identification(BaseModel):
    id: str
    type: IdentificationType


class IdentificationUpdate(BaseModel):
    id: str | None
    type: IdentificationType | None


class UpdateNaturalPersonParticipant(BaseModel):
    first_name: str | None
    last_name: str | None
    identification: IdentificationUpdate | None

    async def update_to_persistance(self, participant_id: UUID, persistance):
        return


class NaturalPersonParticipant(BaseModel):
    first_name: str
    last_name: str
    type: Literal[ParticipantType.NATURAL_PERSON]
    identification: Identification

    async def persist_to(self, persistence):
        participant = ParticipantModel(id=uuid4(), is_verified=False)
        person = NaturalPersonModel(first_name=self.first_name, last_name=self.last_name, participant_id=participant.id,
                                    id=uuid4())
        identification = IdentificationModel(type=self.identification.type, value=self.identification.id,
                                             person_id=person.id)
        persistence.add(participant)
        persistence.add(person)
        persistence.add(identification)
        return participant.id


class RetrievedNaturalPerson(NaturalPersonParticipant):
    created_at: datetime
    is_verified: bool

    def is_named(self, first_name, last_name):
        return self.first_name == first_name and self.last_name == last_name

    def has_dni(self, dni):
        return self.identification.type == IdentificationType.DNI and self.identification.id == dni
