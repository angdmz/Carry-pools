from uuid import UUID

from exceptions import ResourceNotFound


class CustomerNotFound(ResourceNotFound):
    def __init__(self, customer_id: UUID):
        super().__init__(f"Customer not found. ID: {customer_id}")