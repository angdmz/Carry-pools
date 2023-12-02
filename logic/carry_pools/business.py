from __future__ import annotations

from datetime import timedelta

from _decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class BaseVestingSchedule(BaseModel):
    name: str
    description: str | None
    company: UUID
    vesting_percentage: Decimal

    def is_named(self, name):
        return self.name == name

    def is_described(self, description):
        return self.description == description

    def vesting_percentage_is(self, vesting_percentage):
        return self.vesting_percentage == vesting_percentage


class TimeBasedVestingSchedule(BaseVestingSchedule):
    period_duration: timedelta
    sequence: int

    def sequence_is(self, sequence):
        return self.sequence == sequence

    def period_duration_is(self, period_duration):
        return self.period_duration == period_duration

    async def persist_to(self, repository):
        pass


class Milestone(BaseModel):
    name: str


class MilestoneBasedVestingSchedule(BaseVestingSchedule):
    milestone: Milestone
    is_accelerated: bool = False

    async def persist_to(self, session):
        pass


class AcceleratedMilestonBasedVestingSchedule(MilestoneBasedVestingSchedule):
    is_accelerated: bool = True


class VestingSchedule(BaseModel):
    __root__: MilestoneBasedVestingSchedule | AcceleratedMilestonBasedVestingSchedule | TimeBasedVestingSchedule

    def is_named(self, name):
        return self.__root__.is_named(name)

    async def persist_to(self, repository):
        return await self.__root__.persist_to(repository)
