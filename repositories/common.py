from sqlalchemy.ext.asyncio import AsyncSession

class Persistable:
    @classmethod
    def build_from(cls, buildable):
        return cls.parse_obj(buildable.dict())


class BaseRepository:
    
    def __init__(self, async_session: AsyncSession):
        self.async_session = async_session
