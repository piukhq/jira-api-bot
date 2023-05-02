import json
from typing import Union

import pendulum
import requests
from sqlalchemy import select

from db.session import Session
from jira.references import (
    SPRINT_JIRA_FIELD,
    SQUAD_IDENTIFIERS,
    STORY_POINT_JIRA_FIELD,
    TECHNICAL_TICKET_LABEL_LIST,
    JiraSquadID,
)
from models.sprint import Sprint
from models.ticket import Project, Ticket
from projects import PROJECT_LIST, SQUAD_BASE
from settings import JIRA_API_SECRET, JIRA_EMAIL


def get_ticket_type(ticket_info: dict) -> str:
    return ticket_info["fields"]["issuetype"]["name"].lower()


def format_labels(labels: list) -> Union[None, str]:
    if labels:
        labels = json.dumps(labels)
    else:
        labels = None

    return labels


def get_tech_categories_by_ticket(ticket_info: dict) -> list:
    tech_labels = []
    ticket_labels = ticket_info["fields"]["labels"]
    for label in ticket_labels:
        label = label.lower()
        if label in TECHNICAL_TICKET_LABEL_LIST:
            if label in ["security", "secops", "msm"]:
                tech_labels.append("security")
            if label == "devops":
                tech_labels.append("devops")
            if not tech_labels:
                tech_labels.append("misc_tech")

    return tech_labels


def get_related_projects_by_ticket(ticket_info: dict, squad_id: JiraSquadID) -> list:
    projects = PROJECT_LIST[squad_id]
    ticket_projects = []
    for project in projects:
        if project.check_ticket_is_part_of_project(ticket_info):
            ticket_projects.append(project.name)

    return ticket_projects


def categorise_ticket(
    ticket_info: dict, sprint: Union[None, Sprint], squad_id: JiraSquadID, from_backlog: bool = False
) -> Ticket:
    ticket_type = get_ticket_type(ticket_info)
    if "investig" in ticket_info["fields"]["summary"].lower():
        ticket_type = "investigation"
    elif ticket_type in ["story"]:
        ticket_type = "user_story"
    elif ticket_type in ["bug"]:
        ticket_type = "bug"
    else:
        print(
            f"ALERT!!!! UNEXPECTED TICKET TYPE: {ticket_type}. Ticket key: {ticket_info['key']}, from_backlog: {from_backlog}, skipping..."
        )

    tech_labels = get_tech_categories_by_ticket(ticket_info)
    project_list = get_related_projects_by_ticket(ticket_info, squad_id)

    product_labels = []
    if project_list:
        product_labels.append("project")
    elif not tech_labels and not project_list:
        product_labels.append("bau_product")

    sprint_finish_date = None
    sprint_id = None
    if sprint:
        sprint_finish_date = sprint.end_date
        sprint_id = sprint.id

    if from_backlog:
        backlog = "True"
        ticket_resolution_date = None
        squad_base = SQUAD_BASE[squad_id]()
        refined = squad_base.is_ticket_refined(ticket_info)
    else:
        backlog = "False"
        refined = "True"
        resolution_date = ticket_info["fields"]["resolutiondate"]
        if resolution_date:
            ticket_resolution_date = pendulum.parse(resolution_date).to_datetime_string()
        else:
            ticket_resolution_date = None
            print(
                f"I'm not expecting tickets with no resolution date on completed sprints! "
                f"Carried over tickets should already be filtered! Check ticket: {ticket_info['key']}"
            )

    return Ticket(
        squad_id=squad_id,
        jira_id=ticket_info["id"],
        jira_ref=ticket_info["key"],
        ticket_type=ticket_type,
        ticket_created_date=pendulum.parse(ticket_info["fields"]["created"]).to_datetime_string(),
        story_points=ticket_info["fields"].get(STORY_POINT_JIRA_FIELD),
        ticket_specific_completed_date=ticket_resolution_date,
        ticket_sprint_completed_date=sprint_finish_date,
        sprint_id=sprint_id,
        tech_labels=format_labels(tech_labels),
        product_labels=format_labels(product_labels),
        project_labels=format_labels(project_list),
        refined=refined,
        backlog=backlog,
    )


def categorise_and_save_sprint_tickets(
    tickets: list, sprint: Sprint, squad_id: JiraSquadID, refined: Union[None, str] = None
) -> None:
    tickets_to_save = []
    sprint_carry_over_ticket_count = 0
    defect_total = 0
    for ticket in tickets:
        sprints = [sprint["id"] for sprint in ticket["fields"][SPRINT_JIRA_FIELD]]

        if len(sprints) > 1:
            if sprint.jira_id != max(sprints):
                sprint_carry_over_ticket_count += 1
                continue
        if ticket["fields"]["status"]["name"].lower() != "done":
            sprint_carry_over_ticket_count += 1
            continue

        ticket_type = get_ticket_type(ticket)
        if ticket_type.lower() in ["sub-task", "defect", "task"]:
            continue

        ticket_to_save = categorise_ticket(ticket, sprint, squad_id, from_backlog=False)

        tickets_to_save.append(ticket_to_save)

        subtasks = ticket["fields"]["subtasks"]
        if subtasks:
            for subtask in subtasks:
                subtask_type = subtask["fields"]["issuetype"]["name"].lower()
                if subtask_type == "defect":
                    defect_total += 1

    with Session() as session:
        session.add_all(tickets_to_save)
        sprint.defect_total = defect_total
        sprint.tickets_carried_over = sprint_carry_over_ticket_count
        session.add(sprint)
        session.commit()

    return


def fetch_sprint_tickets(squad_id: JiraSquadID, sprint: Sprint) -> None:
    count = 0
    page_size = 50
    tickets = []

    while True:
        params = {
            "jql": "status = Done",
            "startAt": count,
            "maxResults": page_size,
        }
        resp = requests.get(
            f"https://hellobink.atlassian.net/rest/agile/1.0/board/{squad_id}/sprint/{sprint.jira_id}/issue",
            auth=(JIRA_EMAIL, JIRA_API_SECRET),
            params=params,
        )

        ticket_response_data = resp.json()["issues"]
        tickets.extend(ticket_response_data)
        count += page_size

        if len(ticket_response_data) < page_size:
            break

    categorise_and_save_sprint_tickets(tickets, sprint, squad_id)
    return


def calculate_ticket_info(tickets: list, project_id: int) -> dict:
    sprint_ticket_data = {
        "technical_ticket_total_count": 0,
        "project_ticket_total_count": 0,
        "bau_ticket_total_count": 0,
        "devops_ticket_total_count": 0,
        "security_ticket_total_count": 0,
        "misc_technical_ticket_total_count": 0,
    }
    for project in SQUAD_IDENTIFIERS[project_id]:
        sprint_ticket_data[f"{project['name']} ticket_total_count"] = 0

    for ticket in tickets:
        ticket_labels = ticket.labels_list
        tech_match = False
        for label in ticket_labels:
            if label in TECHNICAL_TICKET_LABEL_LIST:
                tech_match = True
                sprint_ticket_data["technical_ticket_total_count"] += 1
                if label in ["security", "secops", "msm"]:
                    sprint_ticket_data["security_ticket_total_count"] += 1
                elif label == "devops":
                    sprint_ticket_data["devops_ticket_total_count"] += 1
                else:
                    sprint_ticket_data["misc_technical_ticket_total_count"] += 1

        project_match = False
        for project in SQUAD_IDENTIFIERS[project_id]:
            if project["query_field"] == "components":
                if project["query_value"].lower() in ticket.components_list:
                    project_match = True
                    sprint_ticket_data["project_ticket_total_count"] += 1
                    sprint_ticket_data[f"{project['name']} ticket_total_count"] += 1
            else:
                print(f"UNKNOWN QUERY TYPE: {project['query_field']}")

        if not project_match and not tech_match:
            sprint_ticket_data["bau_ticket_total_count"] += 1

    total_tickets = len(tickets)
    if total_tickets == 0:
        sprint_ticket_data["percent_product_project"] = 0
        sprint_ticket_data["percent_product_bau"] = 0
        sprint_ticket_data["percent_technical"] = 0
        for project in SQUAD_IDENTIFIERS[project_id]:
            sprint_ticket_data[f"percent {project['name']}"] = 0
    else:
        sprint_ticket_data["percent_product_project"] = round(
            (sprint_ticket_data["project_ticket_total_count"] / total_tickets) * 100, 1
        )
        sprint_ticket_data["percent_product_bau"] = round(
            (sprint_ticket_data["bau_ticket_total_count"] / total_tickets) * 100, 1
        )
        sprint_ticket_data["percent_technical"] = round(
            (sprint_ticket_data["technical_ticket_total_count"] / total_tickets) * 100, 1
        )
        for project in SQUAD_IDENTIFIERS[project_id]:
            sprint_ticket_data[f"percent {project['name']}"] = round(
                (sprint_ticket_data[f"{project['name']} ticket_total_count"] / total_tickets) * 100, 1
            )

    return sprint_ticket_data


def count_tickets_by_category_and_project(squad_id: int, ticket_list: list):
    project_list = select(Project).where(Project.jira_squad_id == squad_id)
    with Session() as session:
        project_list = session.execute(project_list).scalars().all()

    project_name_list = [x.name for x in project_list]
    ticket_info = {x: 0 for x in project_name_list}

    ticket_info.update(
        {
            "tech_tickets": 0,
            "security_tickets": 0,
            "devops_tickets": 0,
            "misc_technical_tickets": 0,
            "product_tickets": 0,
            "bau_product": 0,
            "project": 0,
        }
    )

    for ticket in ticket_list:
        tech_labels = ticket.tech_labels
        if tech_labels:
            ticket_info["tech_tickets"] += 1
            tech_labels = json.loads(tech_labels)
            if "security" in tech_labels:
                ticket_info["security_tickets"] += 1
            if "devops" in tech_labels:
                ticket_info["devops_tickets"] += 1
            if "misc_tech" in tech_labels:
                ticket_info["misc_technical_tickets"] += 1

        product_labels = ticket.product_labels
        if product_labels:
            ticket_info["product_tickets"] += 1
            product_labels = json.loads(product_labels)
            if "bau_product" in product_labels:
                ticket_info["bau_product"] += 1
            if "project" in product_labels:
                ticket_info["project"] += 1

        projects = ticket.project_labels
        if projects:
            projects = json.loads(projects)
            for ticket_project in projects:
                ticket_info[ticket_project] += 1

    return ticket_info
