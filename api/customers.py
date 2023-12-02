import http
from datetime import datetime
from typing import Set
from uuid import UUID

from fastapi import APIRouter, Query, Body
from fastapi.params import Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from common import ObjRef
from dependencies.db import get_session
from dependencies.repositories import get_customer_repository
from enums import SortOrder
from logic.customers import Customer
from logic.participants import ListLimit
from repositories.customers import Repository

router = APIRouter()


@router.post("/customers", status_code=http.HTTPStatus.CREATED)
async def create_customer(customer: Customer = Body(..., description="Customer Data"),
                          customer_repository: Repository=Depends(get_customer_repository),
                          session: AsyncSession = Depends(get_session)):
    async with session.begin():
        vesting_schedule_id = await customer_repository.create(customer)
    return ObjRef(id=vesting_schedule_id)


@router.get("/customers/{customer_id}", status_code=http.HTTPStatus.OK)
async def retrieve_customer(customer_id: UUID = Path(..., description="Customer ID"),
                          customer_repository: Repository=Depends(get_customer_repository),
                          session: AsyncSession = Depends(get_session)):

    class RetrievedCustomer(Customer, ObjRef):
        pass

    async with session.begin():
        customer = await customer_repository.retrieve(customer_id)
    d = customer.dict()
    d["id"] = customer_id
    return RetrievedCustomer.parse_obj(d)

@router.patch("/customers/{customer_id}", status_code=http.HTTPStatus.NO_CONTENT)
async def update_customer(customer_id: UUID = Path(..., description="Customer ID"),
                          customer: Customer = Body(..., description="Customer data to update"),
                          customer_repository: Repository=Depends(get_customer_repository),
                          session: AsyncSession = Depends(get_session)):
    async with session.begin():
        vesting_schedule_id = await customer_repository.update(customer_id, customer)


@router.get("/customers", status_code=http.HTTPStatus.OK)
async def list_customers(
        customer_repository: Repository=Depends(get_customer_repository),
        limit: ListLimit = Query(10, description=""),
        sort: SortOrder = Query(SortOrder.DESC, description=""),
        timestamp_gt: datetime | None = Query(
            None, description="Only include customers created with timestamps greater than this value."
        ),
        timestamp_lt: datetime | None = Query(
            None, description="Only include customers created with timestamps less than this value."
        ), session: AsyncSession = Depends(get_session)):
    async with session.begin():
        res = await customer_repository.list(limit=limit, sort=sort, timestamp_gt=timestamp_gt, timestamp_lt=timestamp_lt)
    return res
