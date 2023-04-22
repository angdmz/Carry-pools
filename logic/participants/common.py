from datetime import datetime
from common import ObjRef


class RetrievedParticipantBase(ObjRef):
    created_at: datetime
    is_verified: bool
