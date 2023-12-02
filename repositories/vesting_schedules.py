from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from logic.carry_pools import VestingSchedule, MilestoneBasedVestingSchedule, AcceleratedMilestoneBasedVestingSchedule, TimeBasedVestingSchedule
from models.carry_pools import VestingSchedule as VestingScheduleModel, MilestoneVestingSchedule as MilestoneBasedVestingScheduleModel, TimeBasedVestingSchedule as TimeBasedVestingScheduleModel, Milestone as MilestoneModel
from repositories.common import BaseRepository


class PersistableMilestoneBasedVestingSchedule(MilestoneBasedVestingSchedule):
    async def persist_to(self, session: AsyncSession):
        vesting_schedule_model = VestingScheduleModel(id=uuid4(), company_id=self.company,name=self.name, description=self.description, vesting_percentage=self.vesting_percentage)
        milestone_vesting_schedule = MilestoneBasedVestingScheduleModel(milestone_id=self.milestone, vesting_schedule_id=vesting_schedule_model.id, id=uuid4(), milestone_vesting_percentage=self.vesting_percentage, is_accelerated=self.is_accelerated)
        session.add(vesting_schedule_model)
        session.add(milestone_vesting_schedule)
        return vesting_schedule_model.id


class PersistableTimeBasedVestingSchedule(TimeBasedVestingSchedule):
    async def persist_to(self, session: AsyncSession):
        vesting_schedule_model = VestingScheduleModel(id=uuid4(), company_id=self.company, name=self.name, description=self.description, vesting_percentage=self.vesting_percentage)
        milestone_vesting_schedule = TimeBasedVestingScheduleModel(vesting_schedule_id=vesting_schedule_model.id, id=uuid4(), period_duration=self.period_duration, period_vesting_percentage=self.vesting_percentage, sequence=1)
        session.add(vesting_schedule_model)
        session.add(milestone_vesting_schedule)
        return vesting_schedule_model.id

class PersistableAcceleratedTimeBasedVestingSchedule(PersistableMilestoneBasedVestingSchedule):
    is_accelerated = True


class PersistableVestingSchedule(VestingSchedule):
    __root__: PersistableTimeBasedVestingSchedule | PersistableAcceleratedTimeBasedVestingSchedule | PersistableMilestoneBasedVestingSchedule

    async def persist_to(self, repository):
        return await self.__root__.persist_to(repository)

    @classmethod
    def build_from(cls, vesting_schedule: VestingSchedule):
        return cls.parse_obj(vesting_schedule.dict())


class Repository(BaseRepository):

    RETRIEVE_QUERY = None

    async def persist(self, vesting_schedule: VestingSchedule):
        persistable = PersistableVestingSchedule.build_from(vesting_schedule)
        return await persistable.persist_to(self.async_session)

    async def retrieve(self, vesting_schedule_id: UUID):
        return

    async def list(self):
        pass