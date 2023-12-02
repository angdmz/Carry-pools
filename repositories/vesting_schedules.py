from sqlalchemy.ext.asyncio import AsyncSession


class Repository:

    def __init__(self, async_session: AsyncSession):
        self.async_session = async_session


class TimeBased(Repository):

    async def create(self):
        pass