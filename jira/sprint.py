import requests
from pendulum import parse
from sqlalchemy import select

from db.session import Session
from jira.references import JiraSquadID, SprintStatus
from jira.ticket import (count_tickets_by_category_and_project,
                         fetch_sprint_tickets)
from models.sprint import Sprint
from settings import JIRA_API_SECRET, JIRA_EMAIL


def fetch_completed_sprints(squad_id: JiraSquadID) -> None:
    count = 0
    page_size = 50
    all_sprints = []
    while True:
        params = {
            "startAt": count,
            "maxResults": page_size,
            "state": SprintStatus.CLOSED,
        }
        resp = requests.get(
            f"https://hellobink.atlassian.net/rest/agile/1.0/board/{squad_id}/sprint",
            auth=(JIRA_EMAIL, JIRA_API_SECRET),
            params=params,
        )

        sprints = resp.json()["values"]
        all_sprints.extend(sprints)
        count += page_size

        if len(sprints) < page_size:
            break

    sprints_to_save = []
    for sprint in all_sprints:
        if parse(sprint["startDate"]) > parse("2021-01-01") and sprint["endDate"]:
            sprint_to_save = Sprint(
                squad_id=squad_id,
                jira_id=sprint["id"],
                name=sprint["name"],
                goal=sprint["goal"],
                start_date=parse(sprint["startDate"]).to_datetime_string(),
                end_date=parse(sprint["endDate"]).to_datetime_string(),
                status=SprintStatus.CLOSED,
            )
            sprints_to_save.append(sprint_to_save)

    with Session() as session:
        session.add_all(sprints_to_save)
        session.commit()

    return


def fetch_sprints_and_sprint_tickets(squad_id: JiraSquadID) -> None:
    print(f"Fetching sprints for project: {squad_id}")

    fetch_completed_sprints(squad_id)
    with Session() as session:
        select_sprints_query = select(Sprint).filter(Sprint.status == SprintStatus.CLOSED, Sprint.squad_id == squad_id)
        sprints = session.execute(select_sprints_query).scalars().all()

    print("Fetched sprints, now fetching tickets...")
    for sprint in sprints:
        fetch_sprint_tickets(squad_id, sprint)

    print("Data is up to date!")
    return


def catagorise_sprint_tickets(squad_id: int) -> list:
    with Session() as session:
        sprint_query = select(Sprint).where(Sprint.squad_id == squad_id)
        completed_sprints = session.execute(sprint_query).scalars().all()

    print("Collected sprint data, Now organising...")
    squad_data = []
    for sprint in completed_sprints:
        sprint_info = {
            "name": sprint.name,
            "goal": sprint.goal,
            "start_date": sprint.start_date,
            "end_date": sprint.end_date,
            "ticket_total": sprint.count_all_tickets(),
            "ticket_carry_over_count": sprint.tickets_carried_over,
            "user_story_count": sprint.count_tickets_by_type("user_story"),
            "investigation_count": sprint.count_tickets_by_type("investigation"),
            "bug_count": sprint.count_tickets_by_type("bug"),
            "defect_count": sprint.defect_total,
        }

        ticket_list = sprint.get_all_tickets()
        ticket_count_by_category_and_project = count_tickets_by_category_and_project(squad_id, ticket_list)
        sprint_info.update(ticket_count_by_category_and_project)
        squad_data.append(sprint_info)

    return squad_data
