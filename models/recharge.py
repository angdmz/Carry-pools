from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import func, Column, ForeignKey, UniqueConstraint
from sqlalchemy.orm import mapped_column, relationship
from . import BaseModel
from .enums import recharge_status


class Recharge(BaseModel):
    __tablename__ = "recharges"
    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    address_id = mapped_column(ForeignKey("ethereum_accounts.id"), nullable=False)
    address = relationship("Address")


class RechargeStatus(BaseModel):
    __tablename__ = "recharge_statuses"
    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    recharge_id = mapped_column(ForeignKey("recharges.id"), nullable=False)
    recharge = relationship("Recharge")
    status = Column(recharge_status, nullable=False)
    __table_args__ = (UniqueConstraint('recharge_id', 'status', 'created_at', name='recharge_id_status_created_at_uc'),)
