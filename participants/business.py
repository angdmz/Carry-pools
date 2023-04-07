from datetime import datetime, timezone
from typing import Union, List
from uuid import uuid4, UUID

from pydantic import BaseModel, ConstrainedInt
from sqlalchemy import select, asc, desc
from typing_extensions import Literal

from enums import ParticipantType, AcademicType, SortOrder
from models.participants import Participant as ParticipantModel, NaturalPerson as NaturalPersonModel, \
    Identification as IdentificationModel, Company as CompanyModel, GovernmentOrganism as GovernmentOrganismModel, \
    Academic as AcademicModel
from participants.natural_person import UpdateNaturalPersonParticipant, NaturalPersonParticipant, RetrievedNaturalPerson


class CompanyParticipant(BaseModel):
    full_name: str
    cuit: str
    type: Literal[ParticipantType.COMPANY]

    async def persist_to(self, persistence):
        participant = ParticipantModel(id=uuid4(), is_verified=False)
        company = CompanyModel(full_name=self.full_name, cuit=self.cuit, participant_id=participant.id, id=uuid4())
        persistence.add(participant)
        persistence.add(company)
        return participant.id


class RetrievedCompanyParticipant(CompanyParticipant):
    created_at: datetime
    is_verified: bool

    def is_named(self, full_name):
        return self.full_name == full_name

    async def update_to_persistance(self, update_form: dict, persistance):
        return


class GovernmentOrganismParticipant(BaseModel):
    full_name: str
    sector: str
    type: Literal[ParticipantType.GOVERNMENT_ORGANISM]

    async def persist_to(self, persistence):
        participant = ParticipantModel(id=uuid4(), is_verified=False)
        government_organism = GovernmentOrganismModel(full_name=self.full_name, sector=self.sector, id=uuid4(),
                                                      participant_id=participant.id)
        persistence.add(participant)
        persistence.add(government_organism)
        return participant.id


class RetrievedGovernmentOrganismParticipant(GovernmentOrganismParticipant):
    created_at: datetime
    is_verified: bool

    def is_named(self, name):
        return self.full_name == name

    async def update_to_persistance(self, update_form: dict, persistance):
        return


class AcademicParticipant(BaseModel):
    full_name: str
    education_level: AcademicType
    type: Literal[ParticipantType.ACADEMIC]

    async def persist_to(self, persistence):
        participant = ParticipantModel(id=uuid4(), is_verified=False)
        academic = AcademicModel(full_name=self.full_name, education_level=self.education_level, id=uuid4(),
                                 participant_id=participant.id)
        persistence.add(participant)
        persistence.add(academic)
        return participant.id


class RetrievedAcademicParticipant(AcademicParticipant):
    created_at: datetime
    is_verified: bool

    def is_named(self, full_name):
        return self.full_name == full_name


class Participant(BaseModel):
    __root__: Union[NaturalPersonParticipant, GovernmentOrganismParticipant, CompanyParticipant, AcademicParticipant]

    async def persist_to(self, persistence):
        res = await self.__root__.persist_to(persistence)
        return res


MAX_PARTICIPANT_LIST_LIMIT = 1000


class ListLimit(ConstrainedInt):
    ge = 1
    le = MAX_PARTICIPANT_LIST_LIMIT


class UpdateParticipant(BaseModel):
    __root__: Union[UpdateNaturalPersonParticipant]

    async def update_to_persistance(self, participant_id: UUID, persistance):
        query = select(ParticipantModel, CompanyModel, GovernmentOrganismModel, NaturalPersonModel, AcademicModel,
                       IdentificationModel).select_from(ParticipantModel).join(CompanyModel, isouter=True).join(
            GovernmentOrganismModel, isouter=True).join(AcademicModel, isouter=True).join(NaturalPersonModel,
                                                                                          isouter=True).join(
            IdentificationModel, isouter=True).filter(ParticipantModel.id == participant_id)
        res = await persistance.execute(query)

        types = {
            CompanyModel: ParticipantType.COMPANY,
            GovernmentOrganismModel: ParticipantType.GOVERNMENT_ORGANISM,
            AcademicModel: ParticipantType.ACADEMIC,
            NaturalPersonModel: ParticipantType.NATURAL_PERSON,
        }

        participant, company, government, person, academic, identification = res.all()[0]
        res_dict = dict()
        for model in (participant, company, government, person, academic):
            if model:
                res_dict = {**res_dict, **model.__dict__}
                if model.__class__ in types:
                    res_dict["type"] = types[model.__class__]

        if identification:
            res_dict["identification"] = {"id": identification.value, "type": identification.type}

        retrieved = UpdateParticipant.parse_obj(res_dict)
        await retrieved.update_to_persistance(self.__root__.dict(exclude={"created_at"}), persistance)


class RetrievedParticipant(BaseModel):
    __root__: Union[
        RetrievedNaturalPerson, RetrievedGovernmentOrganismParticipant, RetrievedCompanyParticipant, RetrievedAcademicParticipant]

    @staticmethod
    async def from_persistance(participant_id: UUID, persistance):
        query = select(ParticipantModel, CompanyModel, GovernmentOrganismModel, NaturalPersonModel, AcademicModel,
                       IdentificationModel).select_from(ParticipantModel).join(CompanyModel, isouter=True).join(
            GovernmentOrganismModel, isouter=True).join(AcademicModel, isouter=True).join(NaturalPersonModel,
                                                                                          isouter=True).join(
            IdentificationModel, isouter=True).filter(ParticipantModel.id == participant_id)
        res = await persistance.execute(query)

        types = {
            CompanyModel: ParticipantType.COMPANY,
            GovernmentOrganismModel: ParticipantType.GOVERNMENT_ORGANISM,
            AcademicModel: ParticipantType.ACADEMIC,
            NaturalPersonModel: ParticipantType.NATURAL_PERSON,
        }

        participant, company, government, person, academic, identification = res.all()[0]
        res_dict = dict()
        for model in (participant, company, government, person, academic):
            if model:
                res_dict = {**res_dict, **model.__dict__}
                if model.__class__ in types:
                    res_dict["type"] = types[model.__class__]

        if identification:
            res_dict["identification"] = {"id": identification.value, "type": identification.type}

        return RetrievedParticipant.parse_obj(res_dict)

    async def update_to_persistance(self, update_form: dict, persistance):
        await self.__root__.update_to_persistance(update_form, persistance)


class ParticipantListing(BaseModel):
    results: List[Participant]
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

        query = select(ParticipantModel, CompanyModel, GovernmentOrganismModel, NaturalPersonModel, AcademicModel,
                       IdentificationModel).select_from(ParticipantModel).join(CompanyModel, isouter=True).join(
            GovernmentOrganismModel, isouter=True).join(AcademicModel, isouter=True).join(NaturalPersonModel,
                                                                                          isouter=True).join(
            IdentificationModel, isouter=True)

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
            types = {
                CompanyModel: ParticipantType.COMPANY,
                GovernmentOrganismModel: ParticipantType.GOVERNMENT_ORGANISM,
                AcademicModel: ParticipantType.ACADEMIC,
                NaturalPersonModel: ParticipantType.NATURAL_PERSON,
            }

            participant, company, government, person, academic, identification = res
            res_dict = dict()
            for model in (participant, company, government, person, academic):
                if model:
                    res_dict = {**res_dict, **model.__dict__}
                    if model.__class__ in types:
                        res_dict["type"] = types[model.__class__]

            if identification:
                res_dict["identification"] = {"id": identification.value, "type": identification.type}
            returnable.append(RetrievedParticipant.parse_obj(res_dict))

        return ParticipantListing(results=returnable, next_url=None)
