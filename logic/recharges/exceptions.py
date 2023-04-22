from uuid import UUID

from exceptions import ResourceNotFound


class RechargeNotFound(ResourceNotFound):
    def __init__(self, recharge_id: UUID):
        super().__init__(f"Recharge not found: {recharge_id}")
