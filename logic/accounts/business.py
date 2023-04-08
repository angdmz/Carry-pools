import string
from datetime import datetime
from typing import Dict, Any, List
from uuid import uuid4, UUID

from pydantic import BaseModel
from sqlalchemy import select

from enums import AccountControllerStatus
from .exceptions import AccountNotFound
from logic.participants import RetrievedParticipant
from models.accounts import AccountController as AccountControllerModel, Address as AddressModel, AccountControllerStatus as AccountControllerStatusModel
from ..participants.business import RETRIEVE_PARTICIPANT_QUERY, _from_row


class Address(str):

    @classmethod
    def __modify_schema__(cls, field_schema: Dict[str, Any]) -> None:
        field_schema.update(type='string', format='address')

    @classmethod
    def __get_validators__(cls) -> 'CallableGenerator':
        yield cls.validate

    @classmethod
    def validate(cls, value: str) -> 'Address':
        if "0x" != value[0:2] or not set(value[2:]).issubset(string.hexdigits) or len(value) != 42:
            raise ValueError(f"{value} is not valid address")
        return cls(value)


class Account(BaseModel):
    address: Address
    participant_id: UUID

    async def persist_to(self, persistance):
        address = AddressModel(public_key=self.address, id=uuid4())
        controller = AccountControllerModel(address_id=address.id, participant_id=self.participant_id, id=uuid4())
        status = AccountControllerStatusModel(status=AccountControllerStatus.UNVERIFIED, account_controller_id=controller.id)
        persistance.add(address)
        persistance.add(controller)
        persistance.add(status)


class RetrievedAccount(BaseModel):
    address: Address
    created_at: datetime
    controllers: List[RetrievedParticipant]

    @staticmethod
    async def from_persistance(address: Address, persistance):
        query = RETRIEVE_PARTICIPANT_QUERY.add_columns(AccountControllerModel, AddressModel).join(AccountControllerModel).join(AddressModel).filter(AddressModel.public_key == address)
        res = await persistance.execute(query)
        res_all = res.all()
        if len(res_all) > 0:
            retrieved_address = res_all[0][7]
            controllers = [_from_row(res_controller[0:6]) for res_controller in res_all]
            returnable = RetrievedAccount(address=retrieved_address.public_key, created_at=retrieved_address.created_at, controllers=controllers)
            return returnable
        raise AccountNotFound(address)

    def has_controller_identified_as(self, participant_id: UUID):
        return any([participant.is_identified_as(participant_id) for participant in self.controllers])

    def controllers_count_is(self, count):
        return len(self.controllers) == count
