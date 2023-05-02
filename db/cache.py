import pendulum
from sqlalchemy import select
from sqlalchemy.exc import OperationalError

from db.base import recreate_db
from db.session import Session
from jira_enums import Enum
from models.cache import Cache


class CacheIDs(str, Enum):
    SPRINT_REPORT = "sprint_report"


def update_cache(cache_id: CacheIDs):
    cache = Cache(id=cache_id)
    with Session() as session:
        session.add(cache)
        session.commit()


# TODO: update to actual db
def is_cache_outdated(cache_id: CacheIDs) -> bool:
    query = select(Cache).where(Cache.id == cache_id)
    try:
        with Session() as session:
            jira_cache = session.execute(query).scalar()
    except OperationalError:
        jira_cache = None

    if jira_cache:
        refresh_date = pendulum.yesterday()
        last_update = pendulum.parse(jira_cache.last_update)
        if last_update > refresh_date:
            return False
        else:
            print("Cache has expired, attempting to delete DB")
            recreate_db()

    recreate_db()
    return True
