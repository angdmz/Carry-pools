from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from enums import SortOrder
from logic.customers import Customer,  CustomerNotFound, RetrievedCustomer
from models.customers import Customer as CustomerModel
from repositories.common import BaseRepository, Persistable


class PersistableCustomer(Customer, Persistable):

    async def persist_to(self, session: AsyncSession):
        customer = CustomerModel(id=uuid4(), name=self.name)
        session.add(customer)
        return customer.id


class Repository(BaseRepository):

    CUSTOMER_QUERY = select(CustomerModel).select_from(CustomerModel)

    async def create(self, customer: Customer):
        persistable = PersistableCustomer.build_from(customer)
        return await persistable.persist_to(self.async_session)

    async def retrieve(self, customer_id: UUID):
        query = self.CUSTOMER_QUERY.where(CustomerModel.id == customer_id)
        res = await self.async_session.execute(query)
        res_all = res.all()
        if len(res_all) > 0:
            customer_model = res_all[0][0]
            returnable = RetrievedCustomer(
                id=customer_model.id,
                name=customer_model.name,
                created_at=customer_model.created_at,
                updated_at=customer_model.updated_at)
            return returnable
        raise CustomerNotFound(customer_id)


    async def update(self, customer_id: UUID, customer: Customer):
        query = self.CUSTOMER_QUERY.where(CustomerModel.id == customer_id)
        res = await self.async_session.execute(query)
        res_all = res.all()
        if len(res_all) > 0:
            customer_model = res_all[0][0]
            customer_model.name = customer.name
            self.async_session.add(customer_model)
            return
        raise CustomerNotFound(customer_id)

    async def list(self, limit: int = 10, sort: SortOrder = SortOrder.ASC, timestamp_gt: datetime | int | None = None, timestamp_lt: datetime | int | None = None ):
        pass