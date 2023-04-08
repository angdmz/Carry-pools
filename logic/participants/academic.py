from datetime import datetime
from typing import Union
from uuid import uuid4, UUID

from sqlalchemy import select
from typing_extensions import Literal

from pydantic import BaseModel

from enums import AcademicType, ParticipantType
from models import Participant as ParticipantModel, Academic as AcademicModel
from logic.participants.exceptions import ParticipantNotFound


class AcademicParticipantBase(BaseModel):
    full_name: str
    education_level: AcademicType
    type: Literal[ParticipantType.ACADEMIC] = ParticipantType.ACADEMIC

    def is_named(self, name):
        return self.full_name == name


class UniversityParticipant(AcademicParticipantBase):
    education_level: AcademicType = AcademicType.UNIVERSITY


class HighschoolParticipant(AcademicParticipantBase):
    education_level: AcademicType = AcademicType.HIGHSCHOOL


class SchoolParticipant(AcademicParticipantBase):
    education_level: AcademicType = AcademicType.SCHOOL


class AcademicParticipant(BaseModel):
    __root__: Union[UniversityParticipant, HighschoolParticipant, SchoolParticipant]

    async def persist_to(self, persistence):
        participant = ParticipantModel(id=uuid4(), is_verified=False, type=self.__root__.type)
        academic = AcademicModel(full_name=self.__root__.full_name,
                                 education_level=self.__root__.education_level,
                                 id=uuid4(),
                                 participant_id=participant.id)
        persistence.add(participant)
        persistence.add(academic)
        return participant.id


class RetrievedHighschoolParticipant(HighschoolParticipant):
    created_at: datetime
    is_verified: bool
    id: UUID


class RetrievedUniversityParticipant(UniversityParticipant):
    created_at: datetime
    is_verified: bool
    id: UUID


class RetrievedSchoolParticipant(SchoolParticipant):
    created_at: datetime
    is_verified: bool
    id: UUID


class RetrievedAcademicParticipant(AcademicParticipant):
    __root__: Union[RetrievedUniversityParticipant, RetrievedHighschoolParticipant, RetrievedSchoolParticipant]

    def is_named(self, full_name):
        return self.__root__.full_name == full_name

    def is_verified(self):
        return self.__root__.is_verified

    @staticmethod
    def add_columns_to_query(query):
        query = query.add_columns(AcademicModel)
        return query

    @staticmethod
    def add_joins_to_query(query):
        query = query.join(AcademicModel, isouter=True)
        return query

    @staticmethod
    def from_row(row):
        participant, academic = row
        parseable = dict(created_at=participant.created_at, is_verified=participant.is_verified, id=participant.id,
                         full_name=academic.full_name, education_level=academic.education_level)
        return RetrievedAcademicParticipant.parse_obj(parseable)


class UpdateAcademicParticipant(BaseModel):
    full_name: str | None
    education_level: AcademicType | None
    type: Literal[ParticipantType.ACADEMIC] = ParticipantType.ACADEMIC

    async def update_to_persistance(self, participant_id: UUID, persistance):
        values = self.dict(exclude_none=True)
        query = select(AcademicModel).select_from(AcademicModel).filter(AcademicModel.participant_id == participant_id)
        res = await persistance.execute(query)

        try:
            company = res.all()[0][0]
            for field, value in values.items():
                setattr(company, field, value)
        except IndexError:
            raise ParticipantNotFound(participant_id)
