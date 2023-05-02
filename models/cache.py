import pendulum
from sqlalchemy import Column, Text

from db.base import Base


def get_db_date():
    return pendulum.now().to_datetime_string()


class Cache(Base):
    __tablename__ = "cache"

    id = Column(Text, primary_key=True)
    last_update = Column(Text, server_default=get_db_date(), nullable=False)
