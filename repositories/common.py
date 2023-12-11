from datetime import datetime

from sqlalchemy import Select, Column
from sqlalchemy.ext.asyncio import AsyncSession

class Persistable:
    @classmethod
    def build_from(cls, buildable):
        return cls.parse_obj(buildable.dict())


class BaseRepository:
    
    def __init__(self, async_session: AsyncSession):
        self.async_session = async_session


class Filter:
    
    def filter(self, query: Select, column: Column):
        raise NotImplemented("To be implemented")


class TimestampGreaterThan(Filter):
    def __init__(self, value: datetime):
        self.value = value

    def filter(self, query: Select, column: Column):
        return query.filter(column > self.value)


class TimestampLesserThan(Filter):
    def __init__(self, value: datetime):
        self.value = value

    def filter(self, query: Select, column: Column):
        return query.filter(self.value > column)
