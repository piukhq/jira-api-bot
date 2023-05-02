import pendulum

from jira.board import fetch_board_tickets
from jira.references import LOY_STORY_POINT_JIRA_FIELD


def serialise_ticket_info(ticket_data: dict, team: str) -> dict:
    key = ticket_data["key"]
    status = ticket_data["fields"]["status"]["name"]
    if status == "Done":
        last_updated = ticket_data["fields"]["statuscategorychangedate"]
        resolution_date = pendulum.parse(last_updated).to_datetime_string()
    else:
        resolution_date = None

    dev_estimate = 0
    qa_estimate = 0
    if team == "dev":
        dev_estimate = ticket_data["fields"][LOY_STORY_POINT_JIRA_FIELD]
    elif team == "qa":
        qa_estimate = 1

    return {
        "key": key,
        "created_date": pendulum.parse(ticket_data["fields"]["created"]).to_datetime_string(),
        "completed_date": resolution_date,
        "done": True if resolution_date else False,
        "team": team,
        "dev_estimate_story_points": dev_estimate,
        "qa_estimate_story_total": qa_estimate,
    }


def fetch_trusted_channel_information() -> list:
    csv_rows = []

    trusted_channel_dev_jql = (
        'project = "LOY" ' "AND parent in (LOY-2666, LOY-2679, LOY-2684, LOY-2692, LOY-2703) " 'AND type = "Sub-task"'
    )
    dev_tickets = fetch_board_tickets(trusted_channel_dev_jql)
    for ticket_info in dev_tickets:
        serialised_ticket = serialise_ticket_info(ticket_info, "dev")
        csv_rows.append(serialised_ticket)

    trusted_channel_qa_jql = (
        'project = "LOY" '
        'AND "Epic Link" in (LOY-2634, LOY-2635, LOY-2636, LOY-2637, LOY-2638, LOY-2686) '
        'AND type != "Sub-task"'
    )

    qa_tickets = fetch_board_tickets(trusted_channel_qa_jql)
    for ticket_info in qa_tickets:
        serialised_ticket = serialise_ticket_info(ticket_info, "qa")
        csv_rows.append(serialised_ticket)

    return csv_rows
