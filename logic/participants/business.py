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


def _from_row(row):
    types = {
        CompanyModel: ParticipantType.COMPANY,
        GovernmentOrganismModel: ParticipantType.GOVERNMENT_ORGANISM,
        AcademicModel: ParticipantType.ACADEMIC,
        NaturalPersonModel: ParticipantType.NATURAL_PERSON,
    }

    participant, company, government, person, academic, identification = row
    res_dict = dict()
    for model in (participant, company, government, person, academic):
        if model:
            model_dict = model.__dict__
            for k, v in model_dict.items():
                if not k in res_dict:
                    res_dict[k] = v
            if model.__class__ in types:
                res_dict["type"] = types[model.__class__]

    if identification:
        res_dict["identification"] = identification.__dict__
    returnable = RetrievedParticipant.parse_obj(res_dict)
    return returnable


class RetrievedParticipant(BaseModel):
    __root__: Union[RetrievedNaturalPerson, RetrievedGovernmentOrganismParticipant, RetrievedCompanyParticipant, RetrievedAcademicParticipant]

    @staticmethod
    async def from_persistance(participant_id: UUID, persistance):
        query = RETRIEVE_PARTICIPANT_QUERY.filter(ParticipantModel.id == participant_id)
        res = await persistance.execute(query)

        res_all = res.all()
        if len(res_all) > 0:
            returnable = _from_row(res_all[0])
            return returnable
        raise ParticipantNotFound(participant_id)

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
            participant = _from_row(res)
            returnable.append(participant)

        return ParticipantListing(results=returnable, next_url=None)
