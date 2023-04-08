from datetime import datetime, timezone
from typing import Union, List
from uuid import UUID

from pydantic import BaseModel, ConstrainedInt
from sqlalchemy import select, asc, desc

from enums import ParticipantType, SortOrder
from models.participants import Participant as ParticipantModel, NaturalPerson as NaturalPersonModel, \
    Identification as IdentificationModel, Company as CompanyModel, GovernmentOrganism as GovernmentOrganismModel, \
    Academic as AcademicModel

from logic.participants.academic import AcademicParticipant, RetrievedAcademicParticipant, UpdateAcademicParticipant
from logic.participants.company import CompanyParticipant, RetrievedCompanyParticipant, UpdateCompanyParticipant
from logic.participants.exceptions import ParticipantNotFound
from logic.participants.government import GovernmentOrganismParticipant, RetrievedGovernmentOrganismParticipant, \
    UpdateGovernmentOrganismParticipant
from logic.participants.natural_person import UpdateNaturalPersonParticipant, NaturalPersonParticipant, RetrievedNaturalPerson


RETRIEVE_PARTICIPANT_QUERY = select(ParticipantModel,
                                    CompanyModel,
                                    GovernmentOrganismModel,
                                    NaturalPersonModel,
                                    AcademicModel,
                                    IdentificationModel)\
    .select_from(ParticipantModel)\
    .join(CompanyModel, isouter=True)\
    .join(GovernmentOrganismModel, isouter=True)\
    .join(AcademicModel, isouter=True)\
    .join(NaturalPersonModel,isouter=True)\
    .join(IdentificationModel, isouter=True)



MAX_PARTICIPANT_LIST_LIMIT = 1000


class ListLimit(ConstrainedInt):
    ge = 1
    le = MAX_PARTICIPANT_LIST_LIMIT


class Participant(BaseModel):
    __root__: Union[NaturalPersonParticipant, GovernmentOrganismParticipant, CompanyParticipant, AcademicParticipant]

    async def persist_to(self, persistence):
        res = await self.__root__.persist_to(persistence)
        return res


class UpdateParticipant(BaseModel):
    __root__: Union[UpdateNaturalPersonParticipant, UpdateCompanyParticipant, UpdateGovernmentOrganismParticipant, UpdateAcademicParticipant]

    async def update_to_persistance(self, participant_id: UUID, persistance):
        await self.__root__.update_to_persistance(participant_id, persistance)


class RetrievedParticipant(BaseModel):
    __root__: Union[RetrievedNaturalPerson, RetrievedGovernmentOrganismParticipant, RetrievedCompanyParticipant, RetrievedAcademicParticipant]
    _types = {
        ParticipantType.COMPANY: RetrievedCompanyParticipant,
        ParticipantType.GOVERNMENT_ORGANISM: RetrievedGovernmentOrganismParticipant,
        ParticipantType.ACADEMIC: RetrievedAcademicParticipant,
        ParticipantType.NATURAL_PERSON: RetrievedNaturalPerson,
    }

    @staticmethod
    async def from_persistance(participant_id: UUID, persistance):
        new_query = select(ParticipantModel).select_from(ParticipantModel)

        for sub_field in RetrievedParticipant._types.values():
            new_query = sub_field.add_columns_to_query(new_query)
            new_query = sub_field.add_joins_to_query(new_query)
        new_query.filter(ParticipantModel.id == participant_id)
        res = await persistance.execute(new_query)

        res_all = res.all()
        if len(res_all) > 0:
            returnable = RetrievedParticipant.retrieve_participant_from_row(res_all[0])
            return returnable
        raise ParticipantNotFound(participant_id)

    @staticmethod
    def retrieve_participant_from_row(row):
        participant = row[0]
        parser = RetrievedParticipant._types[participant.type]
        the_rest = [column for column in row if column is not None]
        returnable = parser.from_row(the_rest)
        return returnable

    def is_identified_as(self, participant_id):
        return self.__root__.id == participant_id


class ParticipantListing(BaseModel):
    results: List[RetrievedParticipant]
    next_url: str | None

    @staticmethod
    def validate_timestamp_param(timestamp: Union[datetime, int] | None) -> datetime | None:
        if timestamp is None:
            return timestamp
        elif isinstance(timestamp, int):
            timestamp = datetime.fromtimestamp(timestamp, tz=timezone.utc)

        if not isinstance(timestamp, datetime):
            raise TypeError(f"Unsupported timestamp type: {type(timestamp)}")

        if timestamp.tzinfo is None:
            raise ValueError(f"Datetime object provided is missing timezone info: {timestamp}")

        return timestamp


    @staticmethod
    async def from_persistance(persistance, limit: int = 10,
                               verified: bool | None = None,
                               sort: SortOrder = SortOrder.ASC,
                               timestamp_gt: Union[datetime, int] | None = None,
                               timestamp_lt: Union[datetime, int] | None = None, ):
        timestamp_gt = ParticipantListing.validate_timestamp_param(timestamp_gt)
        timestamp_lt = ParticipantListing.validate_timestamp_param(timestamp_lt)

        query = RETRIEVE_PARTICIPANT_QUERY

        if timestamp_gt:
            query = query.filter(ParticipantModel.created_at > timestamp_gt)
        if timestamp_lt:
            query = query.filter(ParticipantModel.created_at < timestamp_lt)

        if verified:
            query = query.filter(ParticipantModel.is_verified == verified)

        if sort == SortOrder.ASC:
            query = query.order_by(asc(ParticipantModel.created_at))
        else:
            query = query.order_by(desc(ParticipantModel.created_at))

        if limit > 0:
            query = query.limit(limit)

        results = await persistance.execute(query)
        all_res = results.all()
        returnable = []
        for res in all_res:
            participant = RetrievedParticipant.retrieve_participant_from_row(res)
            returnable.append(participant)

        return ParticipantListing(results=returnable, next_url=None)
