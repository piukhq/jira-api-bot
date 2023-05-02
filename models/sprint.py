from sqlalchemy import Column, Integer, Text, UniqueConstraint, func, select
from sqlalchemy.orm import relationship

from db.base import Base
from db.session import Session
from models.ticket import Ticket


class Sprint(Base):
    __tablename__ = "sprint"

    id = Column(Integer, primary_key=True)
    squad_id = Column(Integer, index=True)
    jira_id = Column(Integer, index=True)
    name = Column(Text)
    goal = Column(Text)
    start_date = Column(Text, nullable=True)
    end_date = Column(Text, nullable=True)
    status = Column(Text)
    tickets = relationship("Ticket")
    tickets_carried_over = Column(Integer, nullable=True)
    defect_total = Column(Integer, nullable=True)

    __table_args__ = (UniqueConstraint("squad_id", "jira_id", name="jira_id_unq"),)

    def get_all_tickets(self) -> list:
        query = select(Ticket).where(Ticket.sprint_id == self.id)
        with Session() as session:
            ticket_list = session.execute(query).scalars().all()

        return ticket_list

    def count_all_tickets(self) -> int:
        sub_task_types = ["defect"]

        ticket_count_query = select(func.count(Ticket.id)).where(Ticket.sprint_id == self.id)
        with Session() as session:
            all_tickets_total = session.execute(ticket_count_query).scalar()

            sub_task_total = 0
            for task in sub_task_types:
                sub_task_count_query = select(func.count(Ticket.id)).where(
                    Ticket.sprint_id == self.id, Ticket.ticket_type == task
                )
                sub_task_count = session.execute(sub_task_count_query).scalar()
                sub_task_total += sub_task_count

        return all_tickets_total - sub_task_total

    def count_tickets_by_type(self, ticket_type: str) -> int:
        with Session() as session:
            count_query = select(func.count(Ticket.id)).where(
                Ticket.sprint_id == self.id, Ticket.ticket_type == ticket_type
            )
            count = session.execute(count_query).scalar()

        return count
