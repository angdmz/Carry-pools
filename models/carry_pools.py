from sqlalchemy import Column, ForeignKey, UniqueConstraint, Integer
from sqlalchemy.dialects.postgresql import DATERANGE
from sqlalchemy.orm import mapped_column, relationship
from sqlalchemy.types import String, DECIMAL

from .base import BaseModelWithID


class CarryPool(BaseModelWithID):
    __tablename__ = "carry_pools"

    name = Column(String, nullable=False)
    basis_points = Column(DECIMAL, nullable=False)


class Fund(BaseModelWithID):
    __tablename__ = 'funds'

    name = Column(String, nullable=False)
    customer_id = mapped_column(ForeignKey("customers.id"), nullable=False)


class FundCarryPool(BaseModelWithID):
    __tablename__ = 'fund_carry_plans'

    fund_id = mapped_column(ForeignKey("funds.id"), nullable=False)
    carry_pool_id = mapped_column(ForeignKey("carry_pools.id"), nullable=False)
    __table_args__ = (UniqueConstraint('fund_id', 'carry_pool_id', name='fund_id_carry_pool_id_uc'),)


class Deal(BaseModelWithID):
    __tablename__ = 'deals'

    name = Column(String, nullable=False)
    fund_id = mapped_column(ForeignKey("funds.id"), nullable=False)
    capital_deployed = Column(DECIMAL, nullable=True)


class Milestone(BaseModelWithID):
    __tablename__ = 'milestones'

    name = Column(String, nullable=False)
    customer_id = mapped_column(ForeignKey("customers.id"), nullable=False)


class VestingSchedule(BaseModelWithID):
    __tablename__ = 'vesting_schedules'

    customer_id = mapped_column(ForeignKey('customers.id'), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)


class MilestoneVestingSchedule(BaseModelWithID):
    __tablename__ = 'milestone_vesting_schedules'

    vesting_schedule_id = mapped_column(ForeignKey('vesting_schedules.id'), nullable=False)
    milestone_id = mapped_column(ForeignKey('milestones.id'), nullable=False)
    milestone_vesting_percentage = Column(DECIMAL, nullable=False)
    __table_args__ = (UniqueConstraint('vesting_schedule_id', 'milestone_id', name='vesting_schedule_id_milestone_id_uc'),)


class TimeBasedVestingSchedule(BaseModelWithID):
    __tablename__ = 'time_based_vesting_schedules'

    period_duration = Column(DATERANGE(), nullable=False)
    period_vesting_percentage =Column(DECIMAL, nullable=False)
    sequence = Column(Integer, nullable=False)
