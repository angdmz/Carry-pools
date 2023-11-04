from sqlalchemy import Column, ForeignKey, UniqueConstraint
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


class FundCarryPool(BaseModelWithID):
    __tablename__ = 'fund_carry_plans'

    fund = relationship('Fund', back_populates="fund_carry_pools")
    fund_id = mapped_column(ForeignKey("funds.id"), nullable=False)
    carry_pool = relationship('CarryPool', back_populates="fund_carry_pools")
    carry_pool_id = mapped_column(ForeignKey("carry_pools.id"), nullable=False)
    __table_args__ = (UniqueConstraint('fund_id', 'carry_pool_id', name='fund_id_carry_pool_id_uc'),)


class Deal(BaseModelWithID):
    __tablename__ = 'deals'

    name = Column(String, nullable=False)
    fund_id = mapped_column(ForeignKey("funds.id"), nullable=False)
    fund = relationship("Fund", back_populates="deals")
    capital_deployed = Column(DECIMAL, nullable=True)


class Milestone(BaseModelWithID):
    __tablename__ = 'milestones'

    name = Column(String, nullable=False)
