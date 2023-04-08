from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from common import ObjRef


class RetrievedParticipantBase(ObjRef):
    created_at: datetime
    is_verified: bool
