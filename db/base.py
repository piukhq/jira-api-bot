from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base

engine = create_engine("sqlite://")
Base = declarative_base()


def recreate_db():
    print("Recreating DB...")
    Base.metadata.create_all(engine)
    print("DB clear complete!")
