from sqlalchemy.orm import sessionmaker

from db.base import engine

Session = sessionmaker(bind=engine)
