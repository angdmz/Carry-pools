import string
from datetime import datetime
from typing import Dict, Any, List, Literal
from uuid import uuid4, UUID

from asyncpg import Connection
from pydantic import BaseModel, PositiveInt, NonNegativeInt
from sqlalchemy import func, select, Table, Column, Integer, String, Numeric, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.ddl import CreateTable

from common import ObjRef
from enums import AccountControllerStatus
from models import metadata
from .exceptions import AccountNotFound
from logic.participants import RetrievedParticipant
from models.accounts import AccountController as AccountControllerModel, Address as AddressModel, AccountControllerStatus as AccountControllerStatusModel, BalanceLimit as BalanceLimitModel

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
    balance: NonNegativeInt

    async def persist_to(self, persistance, balance_limit):
        address = AddressModel(public_key=self.address, id=uuid4(), balance=self.balance)
        controller = AccountControllerModel(address_id=address.id, participant_id=self.participant_id, id=uuid4())
        balance = BalanceLimitModel(address_id=address.id, amount=balance_limit)
        status = AccountControllerStatusModel(status=AccountControllerStatus.UNVERIFIED, account_controller_id=controller.id)
        persistance.add(address)
        persistance.add(controller)
        persistance.add(balance)
        persistance.add(status)


class Controller(BaseModel):
    status: AccountControllerStatus
    participant: RetrievedParticipant

    def is_identified_as(self, participant_id):
        return self.participant.is_identified_as(participant_id)

    def is_verified(self):
        return self.status == AccountControllerStatus.VERIFIED


class RetrievedController(Controller):
    address: Address
    id: UUID

    @classmethod
    async def from_persistance(cls, address: Address, participant_id: UUID, persistance):
        latest_status_subquery = select(
            AccountControllerStatusModel.account_controller_id,
            func.max(AccountControllerStatusModel.created_at).label("last_status_date"),
        ).select_from(AccountControllerStatusModel).group_by(AccountControllerStatusModel.account_controller_id).subquery()

        query = RetrievedParticipant.get_retrieval_query()\
            .add_columns(AddressModel, AccountControllerModel, AccountControllerStatusModel.status, latest_status_subquery)\
            .join(AccountControllerModel)\
            .join(latest_status_subquery, AccountControllerModel.id == latest_status_subquery.c.account_controller_id)\
            .join(AddressModel)\
            .filter(AddressModel.public_key == address)\
            .filter(AccountControllerModel.participant_id == participant_id)\
            .filter(latest_status_subquery.c.last_status_date == AccountControllerStatusModel.created_at)

        res = await persistance.execute(query)
        res_all = res.all()
        try:
            my_res = res_all[0]
            retrieved_address, account_controller = my_res[6], my_res[7]
            status = my_res[8]
            participant = RetrievedParticipant.retrieve_participant_from_row(my_res[:6])
            returnable = cls(address=retrieved_address.public_key, status=status, participant=participant, id=account_controller.id)
            return returnable
        except IndexError:
            raise AccountNotFound(address)


class VerifiedController(RetrievedController):
    status: Literal[AccountControllerStatus.VERIFIED]


    async def persist_to(self, persistance):
        status = AccountControllerStatusModel(status=AccountControllerStatus.VERIFIED, account_controller_id=self.id)
        persistance.add(status)


class UnverifiedController(RetrievedController):
    status: Literal[AccountControllerStatus.UNVERIFIED]

    def verify(self):
        return VerifiedController.parse_obj({**self.dict(exclude={"status"}), **{"status":AccountControllerStatus.VERIFIED}})


class RetrievedAccount(BaseModel):
    address: Address
    created_at: datetime
    controllers: List[Controller]
    balance: NonNegativeInt
    balance_limit_per_account: NonNegativeInt


    @staticmethod
    async def from_persistance(address: Address, persistance):
        latest_status_subquery = select(
            AccountControllerStatusModel.account_controller_id,
            func.max(AccountControllerStatusModel.created_at).label("last_status_date"),
        ).select_from(AccountControllerStatusModel).group_by(AccountControllerStatusModel.account_controller_id).subquery()

        query = RetrievedParticipant.get_retrieval_query()\
            .add_columns(AccountControllerModel, AccountControllerStatusModel.status, AddressModel, BalanceLimitModel.amount, latest_status_subquery)\
            .join(AccountControllerModel)\
            .join(latest_status_subquery, AccountControllerModel.id == latest_status_subquery.c.account_controller_id)\
            .join(AddressModel).join(BalanceLimitModel)\
            .filter(AddressModel.public_key == address)\
            .filter(latest_status_subquery.c.last_status_date == AccountControllerStatusModel.created_at)
        res = await persistance.execute(query)
        res_all = res.all()
        if len(res_all) > 0:
            retrieved_address = res_all[0][-4]
            balance_limit_per_account = res_all[0][-3]
            controllers = []
            for res_controller in res_all:
                participant_models = res_controller[0:6]
                status = res_controller[7]
                controller = Controller(participant=RetrievedParticipant.retrieve_participant_from_row(participant_models),
                           status=status)
                controllers.append(controller)
            returnable = RetrievedAccount(address=retrieved_address.public_key, created_at=retrieved_address.created_at,
                                          controllers=controllers, balance=retrieved_address.balance,
                                          balance_limit_per_account=balance_limit_per_account)
            return returnable
        raise AccountNotFound(address)

    def has_controller_identified_as(self, participant_id: UUID):
        return any([participant.is_identified_as(participant_id) for participant in self.controllers])

    def controller_identified_as_is_verified(self, participant_id: UUID):
        controller = next(filter(lambda x: x.is_identified_as(participant_id) , self.controllers))
        return controller.is_verified()

    def controllers_count_is(self, count):
        return len(self.controllers) == count

    def balance_limit_is(self, balance_limit_per_account):
        return self.balance_limit_per_account == balance_limit_per_account

    def has_balance(self, balance):
        return self.balance == balance


class AddressWithBalance(BaseModel):
    address: Address
    balance: NonNegativeInt


class AddressCollection(BaseModel):
    addresses: List[AddressWithBalance]

    async def persist_to(self, async_session: Connection):
        temp_table = """
        create table address_balances
            (
                public_key varchar                                             not null
                    constraint address_balances_public_key_uc
                        unique,
                balance    numeric                                             not null
            );
        """

        await async_session.execute(temp_table)
        await async_session.copy_records_to_table("address_balances", records=[(address.address, address.balance) for address in self.addresses])
        await async_session.execute(
            """
                update ethereum_accounts as dest set
                    balance=src.balance
                from
                    address_balances as src
                where dest.public_key=src.public_key
            """
        )
        await async_session.execute("DROP TABLE address_balances")
