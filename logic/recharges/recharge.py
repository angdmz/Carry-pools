import urllib
from datetime import datetime
from typing import List, Union, Set, Optional
from uuid import uuid4, UUID

from pydantic import BaseModel
from sqlalchemy import select, func, asc, desc
from typing_extensions import Literal

from common import ObjRef, Listing
from enums import RechargeStatus, SortOrder
from logic.accounts import Address
from logic.accounts.exceptions import AccountNotFound
from logic.recharges.exceptions import RechargeNotFound
from models import AccountController as AccountControllerModel
from models.recharge import Recharge as RechargeModel, RechargeStatus as RechargeStatusModel
from models.accounts import Address as AddressModel
from models.participants import Participant as ParticipantModel


class Recharge(BaseModel):
    address: Address
    status: RechargeStatus

    @staticmethod
    def waiting_for(address: Address):
        return Recharge(address=address, status=RechargeStatus.WAITING)

    async def persist_to(self, persistance):
        query_address = select(AddressModel).select_from(AddressModel).filter(AddressModel.public_key == self.address)
        res = await persistance.execute(query_address)
        try:
            address_model = res.all()[0][0]
            recharge = RechargeModel(id=uuid4(), address_id=address_model.id)
            recharge_status = RechargeStatusModel(recharge_id=recharge.id, status=RechargeStatus.WAITING)
            persistance.add(recharge)
            persistance.add(recharge_status)
            return recharge.id
        except IndexError:
            raise AccountNotFound(self.address)


class RetrievedRecharge(ObjRef):
    created_at: datetime
    status: RechargeStatus
    address: Address

    def is_for_address(self, address):
        return self.address == address

    @classmethod
    async def from_persistance(cls, recharge_id, persistance):
        query = cls.get_retrieval_query().filter(RechargeModel.id == recharge_id)
        res = await persistance.execute(query)
        try:
            res_all = res.all()[0]
            return cls.retrieve_recharge_from_row(res_all)
        except IndexError:
            return RechargeNotFound(recharge_id)

    async def persist_to(self, persistance):
        recharge_status = RechargeStatusModel(recharge_id=self.id, status=self.status)
        persistance.add(recharge_status)

    @classmethod
    def get_retrieval_query(cls):
        latest_status_subquery = select(
            RechargeStatusModel.recharge_id,
            func.max(RechargeStatusModel.created_at).label("last_status_date"),
        ).select_from(RechargeStatusModel).group_by(RechargeStatusModel.recharge_id).subquery()
        query = select(RechargeModel, AddressModel.public_key, RechargeStatusModel.status, latest_status_subquery).select_from(RechargeModel).join(AddressModel).join(RechargeStatusModel).join(latest_status_subquery, RechargeModel.id == latest_status_subquery.c.recharge_id).filter(RechargeStatusModel.created_at == latest_status_subquery.c.last_status_date)
        return query

    @classmethod
    def retrieve_recharge_from_row(cls, row):
        recharge, address, status = row[0:3]
        return cls(created_at=recharge.created_at, status=status, address=address, id=recharge.id)


class RetrievedWaitingRecharge(RetrievedRecharge):
    status: Literal[RechargeStatus.WAITING]

    async def satisfy(self):
        return RetrievedSatisfiedRecharge.parse_obj({**self.dict(exclude={"status"}), **{"status":RechargeStatus.SATISFIED}})

    async def reject(self):
        return RetrievedRejectedRecharge.parse_obj(
            {**self.dict(exclude={"status"}), **{"status": RechargeStatus.REJECTED}})


class RetrievedRejectedRecharge(RetrievedRecharge):
    status: Literal[RechargeStatus.REJECTED]


class RetrievedSatisfiedRecharge(RetrievedRecharge):
    status: Literal[RechargeStatus.SATISFIED]



class RechargeListing(Listing):
    results: List[RetrievedRecharge]

    @classmethod
    async def from_persistance(cls, persistance,
                               limit: int = 10,
                               sort: SortOrder = SortOrder.ASC,
                               recharge_ids: Optional[Set[UUID]] = None,
                               addresses: Optional[Set[Address]] = None,
                               participant_ids: Optional[Set[UUID]] = None,
                               status: Optional[Set[RechargeStatus]] = None,
                               timestamp_gt: Union[datetime, int] | None = None,
                               timestamp_lt: Union[datetime, int] | None = None, ):
        timestamp_gt = cls.validate_timestamp_param(timestamp_gt)
        timestamp_lt = cls.validate_timestamp_param(timestamp_lt)

        query = RetrievedRecharge.get_retrieval_query().add_columns(AccountControllerModel, ParticipantModel).join(AccountControllerModel).join(ParticipantModel)

        if timestamp_gt:
            query = query.filter(RechargeModel.created_at > timestamp_gt)
        if timestamp_lt:
            query = query.filter(RechargeModel.created_at < timestamp_lt)

        if status:
            query = query.filter(RechargeStatusModel.status.in_(status))

        if recharge_ids:
            query = query.filter(RechargeModel.id.in_(recharge_ids))

        if addresses:
            query = query.filter(AddressModel.public_key.in_(addresses))

        if participant_ids:
            query = query.filter(ParticipantModel.id.in_(participant_ids))

        if sort == SortOrder.ASC:
            query = query.order_by(asc(RechargeModel.created_at))
        else:
            query = query.order_by(desc(RechargeModel.created_at))


        if limit > 0:
            query = query.limit(limit)

        results = await persistance.execute(query)
        all_res = results.all()
        returnable = []
        for res in all_res:
            participant = RetrievedRecharge.retrieve_recharge_from_row(res)
            returnable.append(participant)

        if len(all_res) == 0:
            return cls(results=[], next_url=None)

        next_params = {
            "limit": limit,
            "sort": sort.value,
            "recharge_ids": [x for x in recharge_ids] if recharge_ids else None,
            "addresses": [x for x in addresses] if addresses else None,
            "participant_ids": [x for x in participant_ids] if participant_ids else None,
            "status": [x.value for x in status] if status else None,
            "timestamp_gt": timestamp_gt,
            "timestamp_lt": timestamp_lt,

        }
        if sort == SortOrder.ASC:
            next_params["timestamp_gt"] = returnable[-1].created_at
        else:
            next_params["timestamp_lt"] = returnable[-1].created_at
        next_params = {k: v for k, v in next_params.items() if v is not None}
        next_url = urllib.parse.urlencode(next_params, doseq=True)

        return cls(results=returnable, next_url=next_url)
