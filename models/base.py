from sqlalchemy import Column, TIMESTAMP, func

from session.connection import Base

metadata = Base.metadata


class BaseModel(Base):
    __abstract__ = True

    created_at = Column(TIMESTAMP(timezone=True),
                        nullable=False,
                        server_default=func.current_timestamp(),)
    updated_at = Column(TIMESTAMP(timezone=True),
                        nullable=False,
                        server_default=func.current_timestamp(),
                        onupdate=func.current_timestamp())
