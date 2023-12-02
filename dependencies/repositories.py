from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies.db import get_session
from repositories import VestingScheduleRepository
from repositories import CustomerRepository


def get_vesting_schedule_repository(session: AsyncSession = Depends(get_session)):
    return VestingScheduleRepository(session)

def get_customer_repository(session: AsyncSession = Depends(get_session)):
    return CustomerRepository(session)
