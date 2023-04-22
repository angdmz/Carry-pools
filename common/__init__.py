from datetime import datetime, timezone
from typing import Union
from uuid import UUID

from pydantic import BaseModel


class ObjRef(BaseModel):
    id: UUID


class Listing(BaseModel):
    next_url: str | None

    @staticmethod
    def validate_timestamp_param(timestamp: Union[datetime, int] | None) -> datetime | None:
        if timestamp is None:
            return timestamp
        elif isinstance(timestamp, int):
            timestamp = datetime.fromtimestamp(timestamp, tz=timezone.utc)

        if not isinstance(timestamp, datetime):
            raise TypeError(f"Unsupported timestamp type: {type(timestamp)}")

        if timestamp.tzinfo is None:
            raise ValueError(f"Datetime object provided is missing timezone info: {timestamp}")

        return timestamp
