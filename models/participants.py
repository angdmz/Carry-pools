from sqlalchemy import Column, func
from sqlalchemy.types import String, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID

from session.connection import Base


class Participant(Base):
    __tablename__ = "participants"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    name = Column(String, unique=True)
    created_at = Column(TIMESTAMP(timezone=True),
                        nullable=False,
                        server_default=func.current_timestamp(),)
    updated_at = Column(TIMESTAMP(timezone=True),
                        nullable=False,
                        server_default=func.current_timestamp(),
                        onupdate=func.current_timestamp())
