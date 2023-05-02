from typing import Union

import requests
from sqlalchemy import func, select

from db.session import Session
from jira.references import JiraSquadID
from jira.ticket import categorise_ticket, get_ticket_type
from models.ticket import Project, Ticket
from settings import JIRA_API_SECRET, JIRA_EMAIL


def categorise_and_save_backlog_tickets(tickets: list, squad_id: JiraSquadID) -> None:
    tickets_to_save = []
    for ticket in tickets:
        ticket_type = get_ticket_type(ticket)
        if ticket_type in ["sub-task"]:
            continue

        ticket_to_save = categorise_ticket(ticket, None, squad_id, from_backlog=True)
        tickets_to_save.append(ticket_to_save)

    with Session() as session:
        session.add_all(tickets_to_save)
        session.commit()


def fetch_backlog_tickets(squad_id: JiraSquadID) -> None:
    count = 0
    page_size = 50
    tickets = []
    while True:
        params = {
            "startAt": count,
            "maxResults": page_size,
        }
        resp = requests.get(
            f"https://hellobink.atlassian.net/rest/agile/1.0/board/{squad_id}/backlog",
            auth=(JIRA_EMAIL, JIRA_API_SECRET),
            params=params,
        )

        ticket_response_data = resp.json()["issues"]
        tickets.extend(ticket_response_data)
        count += page_size

        if len(ticket_response_data) < page_size:
            break

    categorise_and_save_backlog_tickets(tickets, squad_id)
    return


def ticket_query(refined: str, ticket_type: Union[str, None], squad_id: JiraSquadID):
    if ticket_type:
        return select(func.count(Ticket.id)).where(
            Ticket.backlog == "True",
            Ticket.refined == refined,
            Ticket.ticket_type == ticket_type,
            Ticket.squad_id == squad_id,
        )
    else:
        return select(func.count(Ticket.id)).where(
            Ticket.backlog == "True", Ticket.refined == refined, Ticket.squad_id == squad_id
        )


def count_tickets_by_category_and_project(squad_id: JiraSquadID, tickets: list, refined_prefix: str):
    project_query = select(Project).where(Project.jira_squad_id == squad_id)
    with Session() as session:
        project_list = session.execute(project_query).scalars().all()

    project_name_list = [x.name for x in project_list]

    ticket_info = {f"{refined_prefix}_{x}": 0 for x in project_name_list}
    ticket_info.update(
        {
            f"{refined_prefix}_tech_tickets": 0,
            f"{refined_prefix}_secops_tickets": 0,
            f"{refined_prefix}_devops_tickets": 0,
            f"{refined_prefix}_misc_technical_tickets": 0,
            f"{refined_prefix}_product_tickets": 0,
            f"{refined_prefix}_bau_product": 0,
            f"{refined_prefix}_project": 0,
        }
    )

    # TODO: refactor into queries
    for ticket in tickets:
        tech_labels = ticket.tech_labels
        if tech_labels:
            ticket_info[f"{refined_prefix}_tech_tickets"] += 1
            tech_labels = tech_labels.split(",")
            if "security" in tech_labels:
                ticket_info[f"{refined_prefix}_secops_tickets"] += 1
            if "devops" in tech_labels:
                ticket_info[f"{refined_prefix}_devops_tickets"] += 1
            if "misc_tech" in tech_labels:
                ticket_info[f"{refined_prefix}_misc_technical_tickets"] += 1

        product_labels = ticket.product_labels
        if product_labels:
            ticket_info[f"{refined_prefix}_product_tickets"] += 1
            product_labels = product_labels.split(",")
            if "bau_product" in product_labels:
                ticket_info[f"{refined_prefix}_bau_product"] += 1
            if "project" in product_labels:
                ticket_info[f"{refined_prefix}_project"] += 1

        projects = ticket.projects
        if projects:
            projects = projects.split(",")
            for ticket_project in projects:
                ticket_info[f"{refined_prefix}_{ticket_project}"] += 1

    return ticket_info


def catagorise_backlog_tickets(squad_id: JiraSquadID) -> list:
    with Session() as session:
        backlog_query = select(Ticket).where(Ticket.squad_id == squad_id, Ticket.backlog == "True")
        backlog_tickets = session.execute(backlog_query).scalars().all()

        refined_total_query = ticket_query("True", None, squad_id)
        refined_user_story_query = ticket_query("True", "user_story", squad_id)
        refined_investigation_query = ticket_query("True", "investigation", squad_id)
        refined_bug_query = ticket_query("True", "bug", squad_id)
        unrefined_total_query = ticket_query("False", None, squad_id)
        unrefined_user_story_query = ticket_query("False", "user_story", squad_id)
        unrefined_investigation_query = ticket_query("False", "investigation", squad_id)
        unrefined_bug_query = ticket_query("False", "bug", squad_id)

        backlog_info = {
            "squad": squad_id,
            "ticket_total": len(backlog_tickets),
            "refined_ticket_total": session.execute(refined_total_query).scalar(),
            "refined_user_story_count": session.execute(refined_user_story_query).scalar(),
            "refined_investigation_count": session.execute(refined_investigation_query).scalar(),
            "refined_bug_count": session.execute(refined_bug_query).scalar(),
            "unrefined_ticket_total": session.execute(unrefined_total_query).scalar(),
            "unrefined_user_story_count": session.execute(unrefined_user_story_query).scalar(),
            "unrefined_investigation_count": session.execute(unrefined_investigation_query).scalar(),
            "unrefined_bug_count": session.execute(unrefined_bug_query).scalar(),
        }

        refined_ticket_data_query = select(Ticket).where(
            Ticket.backlog == "True", Ticket.refined == "True", Ticket.squad_id == squad_id
        )
        refined_ticket_data = session.execute(refined_ticket_data_query).scalars().all()

        unrefined_ticket_data_query = select(Ticket).where(
            Ticket.backlog == "True", Ticket.refined == "False", Ticket.squad_id == squad_id
        )
        unrefined_ticket_data = session.execute(unrefined_ticket_data_query).scalars().all()

    refined_ticket_expanded_data = count_tickets_by_category_and_project(squad_id, refined_ticket_data, "refined")
    unrefined_ticket_expanded_data = count_tickets_by_category_and_project(squad_id, unrefined_ticket_data, "unrefined")

    backlog_info.update(refined_ticket_expanded_data)
    backlog_info.update(unrefined_ticket_expanded_data)

    return [backlog_info]
