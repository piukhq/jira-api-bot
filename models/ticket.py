from sqlalchemy import Column, ForeignKey, Integer, Table, Text, UniqueConstraint
from sqlalchemy.ext.hybrid import hybrid_property

from db.base import Base

project_ticket = Table(
    "project_ticket",
    Base.metadata,
    Column("project_id", ForeignKey("project.id"), primary_key=True),
    Column("ticket_id", ForeignKey("ticket.id"), primary_key=True),
)


class Ticket(Base):
    __tablename__ = "ticket"

    id = Column(Integer, primary_key=True)
    squad_id = Column(Integer, index=True)
    jira_id = Column(Integer)
    jira_ref = Column(Text, unique=True)
    ticket_type = Column(Text, nullable=False)
    ticket_created_date = Column(Text)
    story_points = Column(Integer, nullable=True)
    ticket_specific_completed_date = Column(Text, nullable=True)
    ticket_sprint_completed_date = Column(Text, nullable=True)
    sprint_id = Column(Integer, ForeignKey("sprint.id", ondelete="CASCADE"))
    tech_labels = Column(Text, nullable=True)
    product_labels = Column(Text, nullable=True)
    project_labels = Column(Text, nullable=True)
    refined = Column(Text)
    backlog = Column(Text)

    __table_args__ = (UniqueConstraint("squad_id", "jira_id", name="jira_id_unq"),)

    @hybrid_property
    def is_backlog(self):
        return bool(self.backlog)


class Project(Base):
    __tablename__ = "project"

    id = Column(Integer, primary_key=True)
    jira_squad_id = Column(Integer)
    name = Column(Text, index=True, unique=True, nullable=False)
