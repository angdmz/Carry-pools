from datetime import datetime

from pydantic import BaseModel

from common import ObjRef


class Customer(BaseModel):
    name: str
    
    def is_named(self, name):
        return self.name == name


class RetrievedCustomer(Customer):
    created_at: datetime
    updated_at: datetime
