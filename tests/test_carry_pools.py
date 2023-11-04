from __future__ import annotations

import http
import uuid
from datetime import timedelta
from uuid import UUID

from pydantic import BaseModel
from pydantic.types import Decimal
from starlette.testclient import TestClient

from common import ObjRef

TEST_TIME_BASED_SCHEDULE = "My test time based schedule"

CARRY_POOL_NAME_2 = "some cool new name"

CARRY_POOL_NAME = "My carry pool"
CARRY_POOL_SLUG = CARRY_POOL_NAME


class CarryPool(BaseModel):
    name: str
    slug: str
    basis_points: Decimal


class UpdatableCarryPool(BaseModel):
    name: str | None
    slug: str | None


def test_basic_carry_pool_creation(client: TestClient):
    carry_pool_data = CarryPool.parse_obj(dict(name=CARRY_POOL_NAME, slug=CARRY_POOL_SLUG, basis_points=100))
    res = client.post("/carry-pools", data=carry_pool_data.json())
    assert res.status_code == http.HTTPStatus.CREATED

    carry_pool_id = ObjRef.parse_raw(res.content).id

    get_res = client.get(f"/carry-pools/{carry_pool_id}")

    assert get_res.status_code == http.HTTPStatus.OK
    carry_pool = CarryPool.parse_raw(get_res.content)
    assert carry_pool.is_named(CARRY_POOL_NAME)
    assert carry_pool.slug_is(CARRY_POOL_SLUG)
    assert carry_pool.basis_points_unassigned(100)

    update_data = UpdatableCarryPool.parse_obj({"name": CARRY_POOL_NAME_2})
    update_res = client.patch(f"/carry-pools/{carry_pool_id}", data=update_data.json())
    assert update_res.status_code == http.HTTPStatus.NO_CONTENT

    get_res = client.get(f"/participants/{carry_pool_id}")
    carry_pool = CarryPool.parse_raw(get_res.content)
    assert carry_pool.is_named(CARRY_POOL_NAME_2)
    assert carry_pool.slug_is(CARRY_POOL_SLUG)
    assert carry_pool.basis_points_unassigned(100)


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

class Milestone(BaseModel):
    name: str


class MilestoneBasedVestingSchedule(BaseVestingSchedule):
    milestone: Milestone
    is_accelerated: bool = False

class AcceleratedMilestonBasedVestingSchedule(MilestoneBasedVestingSchedule):
    is_accelerated: bool = True


class VestingSchedule(BaseModel):
    __root__: MilestoneBasedVestingSchedule | AcceleratedMilestonBasedVestingSchedule | TimeBasedVestingSchedule

    def is_named(self, name):
        return self.__root__.is_named(name)


def test_vesting_schedule_management_flow(client: TestClient):
    company_id = uuid.uuid4()
    time_vesting_schedule = TimeBasedVestingSchedule(name=TEST_TIME_BASED_SCHEDULE, company=company_id, vesting_percentage=Decimal(10), description="some description", sequence=0, period_duration=timedelta(weeks=10))
    creation_res = client.post("/vesting-schedules", data=time_vesting_schedule.json())
    assert creation_res.status_code == http.HTTPStatus.CREATED
    vesting_schedule_id = ObjRef.parse_raw(creation_res.content).id

    get_res = client.get(f"/vesting-schedules/{vesting_schedule_id}")
    vesting_schedule: TimeBasedVestingSchedule = TimeBasedVestingSchedule.parse_raw(get_res.content)
    get_res = client.get(f"/vesting-schedules/{vesting_schedule_id}")

    assert get_res.status_code == http.HTTPStatus.OK
    assert vesting_schedule.is_named(CARRY_POOL_NAME)
    assert vesting_schedule.vesting_percentage_is(10)
    assert vesting_schedule.is_described("some description")