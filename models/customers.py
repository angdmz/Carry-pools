from sqlalchemy import Column, String

from models.base import BaseModelWithID


class Customer(BaseModelWithID):
    __tablename__ = "customers"

    name = Column(String, nullable=False)
