from uuid import UUID

from pydantic import BaseModel


class ObjRef(BaseModel):
    id: UUID
